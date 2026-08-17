# Use Cases: Audit Log Configuration Module

## UC-1: Create Audit Record (Happy Path)

### Primary Actor
Auditor / System Administrator / Any authenticated user performing a business transaction

### Preconditions
- User is authenticated and authorized for the source action
- Source entity exists (Company, Partner, Invoice, Voucher, BankAccount, Config)
- AuditLogService is available and configured

### Postconditions
- Audit record created in audit_log table with all required fields
- Audit record is immutable (cannot be modified/deleted via API)
- System performance: < 200ms overhead for audit record creation

### Success End Condition
- Audit record exists in database with valid ID
- All required fields populated: entity_type, entity_id, action, actor_id, changed_at
- before_value and after_value appropriately populated per action type

### Business Rule Compliance
- BR-3: Complete field capture
- BR-4: Actor validation
- BR5: Action enum (closed)

### Terminology
- entity_type: Company | Partner | Invoice | Voucher | BankAccount | Config
- action: CREATE | UPDATE | DELETE | APPROVE | REJECT | SUSPEND | REACTIVATE | DISSOLVE
- actor_id: authenticated user's system user ID

### Main Success Scenario (Basic Flow):
1. User performs business action (e.g., creates Invoice, updates Company status)
2. System triggers AuditLogService.create() with parameters:
   - entity_type = 'Invoice' (or relevant entity)
   - entity_id = [invoice primary key value]
   - action = 'CREATE' (or relevant action)
   - field_name = NULL (whole-entity action) or specific field name
   - before_value = JSON representation of state before change (or NULL)
   - after_value = JSON representation of state after change (or NULL)
   - actor_id = [authenticated user's user ID]
3. AuditLogService validates:
   - entity_type in closed enum ✓
   - action in closed enum ✓
   - actor_id exists and is active ✓
   - before_value/after_value format correct (if applicable) ✓
4. Service begins database transaction:
   - INSERT audit_log record (INSERT ONLY, no UPDATE/DELETE possible)
   - COMMIT both source entity change and audit record
5. Audit record now immutable in database
6. Return success to user (audit overhead transparent)

### Alternative Paths:

#### ALTERNATIVE PATH 1: UPDATE Action with field_change
1. User updates specific field on entity (e.g., Invoice.vat_rate from 0.10 to 0.15)
2. System triggers AuditLogService.create() with:
   - entity_type = 'Invoice'
   - entity_id = [invoice_id]
   - action = 'UPDATE'
   - field_name = 'vat_rate'
   - before_value = '0.10' (JSON string)
   - after_value = '0.15' (JSON string)
   - actor_id = [user_id]
3. Validation passes (field_name valid, before/after values present)
4. Audit record created with full change context
5. User sees confirmation; audit record invisible to user

#### ALTERNATIVE PATH 2: SUSPEND Company
1. System Administrator suspends a Company
2. AuditLogService.create() called with:
   - entity_type = 'Company'
   - entity_id = [company_id]
   - action = 'SUSPEND'
   - field_name = NULL (whole-entity action)
   - before_value = '{"status": "ACTIVE"}' (JSON)
   - after_value = '{"status": "SUSPENDED"}' (JSON)
   - actor_id = [admin_user_id]
3. All fields validated
4. Audit record created capturing the suspension event
5. Audit trail now includes who suspended which company and when

### Exception Paths:

#### EXCEPTION PATH 1: Unauthorized actor_id
1. User performs action, but actor_id does not reference active user
2. AuditLogService.validate_actor_id() returns error
3. **System Response**: Reject audit record creation
4. **Error**: "Invalid actor_id: user not found or inactive"
5. **Fallback**: Source action proceeds without audit record (logged as security event)
6. **Alert**: Security alert: "Attempted audit record creation with invalid actor_id"

#### EXCEPTION PATH 2: Invalid entity_type
1. System attempts to create audit record with entity_type = 'NonExistent'
2. AuditLogService.validate_entity_type() returns error
3. **System Response**: Reject audit record creation
4. **Error**: "Invalid entity_type: must be one of [Company, Partner, Invoice, Voucher, BankAccount, Config]"
5. **Fallback**: Source action may proceed or fail independently of audit
6. **Alert**: "Invalid entity_type in audit attempt: NonExistent"

#### EXCEPTION PATH 3: Invalid action
1. AuditLogService.create() called with action = 'NONEXISTENT'
2. Validation fails: action not in closed enum
3. **System Response**: Reject audit record creation
4. **Error**: "Invalid action: must be one of [CREATE, UPDATE, DELETE, APPROVE, REJECT, SUSPEND, REACTIVATE, DISSOLVE]"
5. **Fallback**: Source action proceeds without audit record
6. **Alert**: "Invalid action in audit attempt: NONEXISTENT"

#### EXCEPTION PATH 4: Missing required fields
1. AuditLogService.create() called without actor_id
2. Validation: actor_id required and must be active user
3. **System Response**: Reject; log security event
4. **Error**: "Validation failed: actor_id is required"
5. **Fallback**: Source action proceeds; audit record not created
6. **Alert**: "Audit creation failed: missing required field actor_id"

#### EXCEPTION PATH 5: Database constraint violation
1. AuditLogService.begin_transaction() attempts INSERT audit_log
2. Database trigger or constraint blocks INSERT (unlikely in normal operation)
3. **System Response**: Transaction rollback
4. **Error**: "Database error: could not create audit record"
5. **Fallback**: Source entity change rolled back; both source and audit undone
6. **Alert**: "Critical: audit record creation failed; source transaction rolled back. Requires manual review."

#### EXCEPTION PATH 6: SoD violation attempt
1. System Administrator (SA) attempts direct DB UPDATE on audit_log
2. Database trigger prevents UPDATE, returns error
3. **System Response**: Error returned, access logged to separate security audit trail
4. **Error**: "SoD violation: System Administrator cannot modify audit records"
5. **Fallback**: Audit record remains immutable; operation blocked
6. **Alert**: "Critical SoD violation attempted by SA [ID] at [timestamp]" → PagerDuty/Slack alert

#### EXCEPTION PATH 7: Retention policy conflict
1. Retention policy job attempts to archive/delete records
2. System finds records younger than minimum retention threshold
3. **System Response**: Skip records younger than threshold; log skipped count
4. **Error**: None (expected behavior) - records correctly preserved
5. **Fallback**: Records remain in hot storage; job continues with next batch
6. **Alert**: None (normal operation)

#### EXCEPTION PATH 8: Integrity chain discrepancy
1. Daily integrity verification job runs verify_audit_chain()
2. SHA-256 chain discrepancy detected at record N
3. **System Response**: 
   - Flag discrepancy in integrity report
   - Alert PagerDuty/Slack: "Audit chain discrepancy at record N"
   - Generate incident ticket for AA investigation
4. **Fallback**: System continues operation; manual review required
5. **Alert**: Critical - "Audit integrity chain broken at record N, expected hash H1, got H2"
6. **Recovery**: Restore from last known good backup; re-verify; if unfixable, escalate to compliance

## UC-2: Query Audit Records

### Primary Actor
Auditor with 'audit:READ' permission

### Preconditions
- User has READ permission on audit_log (SoD enforcement)
- Audit records exist in system

### Postconditions
- Query returns paged results matching filter criteria
- Results include: all audit record fields + user names (not just IDs)

### Success End Condition
- Audit records displayed/filtered as requested
- Pagination works correctly
- Export functionality available if needed

### Business Rule Compliance
- BR-3: Complete field capture (results show all fields)
- BR-5: SoD (only authorized users can query)

### Main Success Scenario (Basic Flow):
1. Auditor navigates to Audit Log query interface
2. Auditor specifies filter criteria:
   - entity_type = 'Invoice'
   - action = 'UPDATE'
   - start_date = '2026-01-01'
   - end_date = '2026-01-31'
   - actor_id = specific user (optional)
   - page = 1, page_size = 50
3. System queries audit_log with filters applied via indexed columns
4. Results returned: 50 records matching criteria, paginated
5. Auditor reviews records; each shows:
   - Date/Time, Entity Type, Entity ID, Action, Field Changed, Before/After, User Name, IP, Timestamp
6. Auditor clicks "Export" if needed

### Alternative Paths:

#### ALTERNATIVE PATH 1: No records match criteria
1. Auditor applies filters with no matching records (e.g., date range in future)
2. System returns: "No audit records found matching criteria"
3. No pagination displayed (0 records)
4. Auditor adjusts criteria and re-queries

#### ALTERNATIVE PATH 2: Invalid filter parameters
1. Auditor provides invalid entity_type (e.g., 'NonExistent')
2. System validates filter before query
3. **Response**: "Invalid filter: entity_type must be one of [Company, Partner, Invoice, Voucher, BankAccount, Config]"
4. Auditor corrects filter and re-queries

#### ALTERNATIVE PATH 3: Large result set exceeding page size
1. Auditor queries without date filter; results = 5,000+ records
2. System returns first page (50 records) with pagination controls
3. Auditor can navigate pages: 1, 2, 3, ..., 100
4. Auditor can adjust page_size (if permitted) or apply more filters

### Exception Paths:

#### EXCEPTION PATH 1: Unauthorized query attempt
1. User without 'audit:READ' permission attempts to query audit logs
2. Authorization check fails
3. **Response**: 403 Forbidden
4. **Error**: "Access denied: audit:READ permission required"
5. **Fallback**: User cannot view audit records
6. **Alert**: "Unauthorized audit access attempt by user [ID]"

#### EXCEPTION PATH 2: Query performance timeout
1. Auditor queries without date range; results = 10M+ records
2. System applies default date filter (last 3 years) or times out after 30s
3. **Response**: "Query too broad: please add date range filter for performance"
4. **Fallback**: User adds date filter and re-queries
5. **Alert**: "Broad audit query attempted by user [ID]; guided to filtered query"

#### EXCEPTION PATH 3: Export failure
1. Auditor initiates export; system fails (disk space, permission issue)
2. **Response**: "Export failed: [technical reason]"
3. **Fallback**: Try again; contact administrator if persistent
4. **Alert**: "Audit export failure: [reason]; admin notified if persistent"

## UC-3: Verify Audit Log Integrity

### Primary Actor
Compliance Officer / IT Security Manager with 'audit:VERIFY' permission

### Preconditions
- User has VERIFY permission (SoD: separate from READ/WRITE)
- Audit chain exists (at least one record)

### Postconditions
- Integrity verification report generated
- Chain validity status displayed (valid/invalid)
- Root hash shown; discrepancies listed if any

### Success End Condition
- Verification report generated with all required fields
- If valid: "Audit chain integrity confirmed"
- If invalid: Discrepancies identified and reported

### Business Rule Compliance
- BR8: Hash chain integrity
- BR-5: SoD (only VERIFY-permitted users can run verification)

### Main Success Scenario (Basic Flow):
1. Compliance Officer navigates to Integrity Verification page
2. Officer clicks "Verify Chain"
3. System runs background job: verify_audit_chain()
4. Job iterates through all records computing SHA-256 chaining:
   - Record 1: hash_1 = SHA256("root_salt + record1_data")
   - Record 2: hash_2 = SHA256(hash_1 + record2_data)
   - Record 3: hash_3 = SHA256(hash_2 + record3_data)
   - ...continuing to last record...
5. Job validates: for each record N > 1, expected_hash = SHA256(prev_hash + current_data), if expected_hash != current_record.hash → discrepancy
6. Results generated:
   - Chain valid: true/false
   - Root hash: SHA256 of first record's data
   - Total records checked: N
   - Discrepancies: count and locations
   - Verified at: timestamp
7. Report displayed; Officer downloads integrity report

### Alternative Paths:

#### ALTERNATIVE PATH 1: Empty audit log
1. No audit records exist in system
2. System returns: "No audit records to verify"
3. Verification skipped; no report generated
4. Officer notified: "No audit records found; nothing to verify"

#### ALTERNATIVE PATH 2: Chain valid (most common)
1. Chain verification completes with no discrepancies
2. **Report**: "Audit chain integrity: VALID"
3. Root hash displayed
4. Records checked count displayed
5. Officer downloads valid-report.pdf

#### ALTERNATIVE PATH 3: Chain invalid (rare - security incident)
1. Discrepancy detected at record N
2. **Report**: "Audit chain integrity: INVALID - discrepancy at record N"
3. Expected hash vs actual hash displayed
4. Records checked count displayed
5. Officer escalates to IT Security + Compliance
6. Incident ticket created automatically

### Exception Paths:

#### EXCEPTION PATH 1: Insufficient permissions
1. User without 'audit:VERIFY' permission attempts verification
2. **Response**: 403 Forbidden
3. **Error**: "Access denied: audit:VERIFY permission required"
4. **Fallback**: User cannot verify integrity
5. **Alert**: "Unauthorized integrity verification attempt by user [ID]"

#### EXCEPTION PATH 2: Verification timeout (extremely large dataset)
1. Dataset = 10M+ records; verification exceeds 24h timeout
2. **Response**: "Verification in progress; large dataset may take extended time"
3. **Fallback**: Job continues in background; notification sent when complete
4. **Alert**: "Large-scale integrity verification started: [record count] records"

#### EXCEPTION PATH 3: Chain broken - recovery required
1. Discrepancy detected at record N
2. System cannot auto-recover (by design - immutable)
3. **Report**: "INVALID - manual recovery required"
4. **Action**: Restore from last known good backup
5. **Escalation**: Compliance Officer + IT Security immediate notification
6. **Recovery procedure**: 
   - Identify last valid record
   - Restore backup from before discrepancy
   - Re-verify entire chain
   - If unfixable: escalate to regulatory body, document incident

## UC-4: Configure Retention Policy

### Primary Actor
System Administrator with 'system:configure' permission

### Preconditions
- User has retention configuration permission
- Understanding that minimum 10 years is immutable

### Postconditions
- Retention policy configured (or attempted)
- Confirmation displayed with next scheduled actions
- SoD checks enforced

### Success End Condition
- Retention policy updated/confirmed
- Next archival/deletion jobs scheduled
- User informed of immutable minimum

### Business Rule Compliance
- BR-2: Minimum retention 10 years
- BR-9: IP/user capture on config changes
- BR-5: SoD (SA can configure, AA cannot)

### Main Success Scenario (Basic Flow):
1. System Administrator navigates to Retention Policy configuration
2. System displays current policy:
   - Minimum retention: 10 years (immutable, per law)
   - Default: 10 years for all entity types
   - Archival threshold: 3 years (hot → warm)
   - Deletion threshold: 10 years (secure destruction)
3. Administrator views entity-specific retention (all show 10 years, non-changeable)
4. Administrator acknowledges: "Minimum 10 years cannot be reduced without compliance approval"
5. Administrator makes any allowed changes (if any within law; typically none)
6. System saves configuration; schedules next jobs
7. Confirmation displayed: "Retention policy updated. Next archival: 2026-04-15"

### Alternative Paths:

#### ALTERNATIVE PATH 1: Attempt to reduce minimum retention
1. Administrator attempts to set minimum retention = 5 years
2. System validation: "Minimum retention cannot be below 10 years per Luật Kế toán 2015"
3. **Response**: Error displayed; change rejected
4. **Fallback**: Minimum remains at 10 years; administrator must seek compliance approval if truly needed
5. **Alert**: "Retention policy change rejected: minimum 10 years mandated by law"

#### ALTERNATIVE PATH 2: Configure entity-specific retention (if permitted)
1. Administrator attempts to set Company: 5 years, Invoice: 7 years
2. System validation: "Entity-specific retention cannot be below minimum of 10 years"
3. **Response**: Changes rejected for any entity below 10 years
4. **Fallback**: All entities remain at 10 years minimum
5. **Alert**: "Retention change rejected for Company: minimum 10 years"

### Exception Paths:

#### EXCEPTION PATH 1: Administrator without permission
1. User without 'system:configure' attempts to access retention config
2. **Response**: 403 Forbidden
3. **Error**: "Access denied: system:configure permission required"
4. **Fallback**: User cannot configure retention
5. **Alert**: "Unauthorized retention config attempt by user [ID]"

#### EXCEPTION PATH 2: System error saving configuration
1. Save attempt fails (database error, concurrent modification)
2. **Response**: "Failed to save retention policy: [technical reason]"
3. **Fallback**: Roll back; display error; try again
4. **Alert**: "Retention policy save error; admin notified if persistent"

#### EXCEPTION PATH 3: Job scheduling conflict
1. Retention policy save triggers job scheduling
2. Conflict with existing scheduled job (e.g., backup job)
3. **Response**: "Conflict detected: postponing job scheduling"
4. **Fallback**: Schedule jobs at next available window; inform administrator
5. **Alert**: "Job scheduling conflict; resolved at next maintenance window"

## UC-5: SoD Violation Detection and Alert

### Primary Actor
IT Security Manager / Compliance Officer (monitoring role)

### Preconditions
- SoD enforcement active (database roles + application checks)
- Monitoring system operational

### Postconditions
- Violation detected and logged
- Alert sent to appropriate channels
- Incident documented

### Success End Condition
- SoD violation recorded
- Alert dispatched
- Access blocked (if attempted operation)

### Business Rule Compliance
- BR7: SoD enforcement
- BR-5: Separation of duties

### Main Success Scenario (Basic Flow):
1. System Administrator attempts direct UPDATE on audit_log table via database client
2. Database trigger blocks UPDATE; returns error to SA
3. Application logs the attempt with full context:
   - User ID: [SA user ID]
   - Action: UPDATE on audit_log
   - Timestamp: [exact time]
   - Attempted operation: Modify audit record
4. SoD monitoring detects violation (either DB trigger error or app-level check)
5. Violation logged to separate security audit trail (different from business audit_log)
6. Alert dispatched:
   - PagerDuty: "SoD violation: SA [ID] attempted audit record modification"
   - Slack #security-alerts: "@security_team SoD violation detected..."
7. Compliance Officer notified within 24 hours
8. Incident ticket created in tracking system
9. Access review scheduled; SA's audit permissions reviewed

### Alternative Paths:

#### ALTERNATIVE PATH 1: Application-level SoD check blocks operation
1. SA attempts via application API: POST /api/audit/log with unauthorized intent
2. Application check: "SA role cannot have audit:write permission"
3. **Response**: 403 Forbidden
4. **Error**: "SoD violation: System Administrator cannot write audit records"
5. **Fallback**: Operation blocked; audit log of the attempt still created
6. **Alert**: Same as above

#### ALTERNATIVE PATH 2: SoD violation via direct SQL
1. SA executes raw SQL: UPDATE audit_log SET modified = 1 WHERE id = 123
2. Database trigger: prevents UPDATE, returns error " violates trigger 'audit_log_immutability'"
3. **Response**: SQL error, operation blocked
4. **Fallback**: Attempt logged, alert dispatched as above
5. **Alert**: Same as above (different path to same result)

#### ALTERNATIVE PATH 3: No violation (legitimate operation)
1. AA performs READ-only operation on audit_log
2. **Response**: Operation allowed; no alert
3. **Fallback**: AA can view/export audit records as part of role
4. **Alert**: None (normal operation)

### Exception Paths:

#### EXCEPTION PATH 1: False positive SoD alert
1. Legitimate operation triggers SoD monitor (e.g., AA viewing audit records)
2. Monitor incorrectly flags as violation
3. **Response**: Investigation; determine it was false positive
4. **Correction**: Adjust monitoring thresholds if needed
5. **Alert**: "False positive SoD alert resolved: [details]" (for logging only)

#### EXCEPTION PATH 2: Multiple violations in short time
1. Several SA attempted SoD violations within 1 hour
2. **Response**: Batch alert; heightened scrutiny
3. **Escalation**: IT Security Manager reviews all SA actions for 24h period
4. **Alert**: "Multiple SoD violations detected: [count] in last hour; escalation initiated"

#### EXCEPTION PATH 3: Monitoring system down
1. SoD monitor/service unavailable
2. **Response**: Operations continue; alert deferred
3. **Fallback**: Manual review scheduled; service restoration priority
4. **Alert**: "SoD monitoring service temporarily unavailable; resuming when restored"

---