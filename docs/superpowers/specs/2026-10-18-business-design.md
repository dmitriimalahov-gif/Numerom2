# NumerOM Business 250

## Intent and scope
Owner-facing mobile section in the existing application, in the top-left menu. Import up to 250 employees from Excel, maintain an employee directory, build named groups for concrete business tasks, and export a comprehensive report. Preserve the calm light NumerOM style and existing accounts.

## Decision boundary
Names and dates of birth are identifiers, never inputs to employment suitability, ranking, hiring, position assignment or team compatibility. Do not infer professional potential or personality from numerology. The business engine uses only explicit job-related skills, experience notes, interests and availability; unknown evidence stays unknown. No automated hiring decisions or overall employee score. Symbolic personal NumerOM calculations remain in the existing self-reflection sections and are not attached to business recommendations.

## Defaults chosen for implementation
- One private business workspace per authenticated account, independently activated as Business 250. Pilot access costs 0; no invented commercial price or Stripe charge. Commercial billing requires a separately configured offer.
- XLSX and UTF-8 CSV import, max 5 MiB compressed, bounded archive expansion and worksheet dimensions, no macros/formulas/external links. Legacy XLS clearly rejected with a save-as-XLSX instruction.
- Required name/surname, optional DOB (DD.MM.YYYY or ISO/excel date); date is allowed for directory identity, not scoring. Optional department, role, skills separated by semicolons, experience, interests, available hours per week. Fixed header aliases, Russian template and sample.
- Preview with original row numbers, errors and duplicate warnings; nothing persists until the owner confirms a valid import. No silent truncation or partial acceptance. Max 250 employees across workspace, exact duplicates rejected; duplicate names alone are flagged for review, not silently merged.
- Employee edit and removal; group names/task description/required skills/target hours/selected employee IDs, max 50 groups, 20 members per group. Owner manually picks members; report shows per-skill coverage and gaps, declared capacity, missing evidence and practical next steps. Labels distinguish entered evidence from computed coverage.
- Private owner-scoped MongoDB document with optimistic revision checks, bounded idempotent import, no public file links and no third-party LLM transmission. Imports processed in memory; raw files not retained.
- Searchable and paged employee list, detail editor, saved groups, print/PDF report via existing report delivery. Data cleared on account changes; stale async results ignored.

## Acceptance
250 valid employees accepted; 251 rejected; invalid rows/formulas/oversized archives rejected; dates normalized; duplicates surfaced. Cross-owner access denied. Concurrent writes fail cleanly; retrying committed import cannot duplicate records. Changing name/DOB cannot change group coverage. Mobile at 320/390 px; route published and direct reload works. Existing tests and typecheck stay green. Public launch only after backend and frontend parity is verified on a synthetic isolated workspace.

## Wire contract (v1)
EmployeeInput: {name:string,surname:string,birth_date:string|null,department:string,role:string,skills:string[],experience:string,interests:string[],hours_per_week:number|null}. Employee adds id. GroupInput: {name:string,task:string,required_skills:string[],target_hours:number|null,member_ids:string[]}. Group adds id. Workspace: {id,company_name,revision,employees:Employee[],groups:Group[],created_at,updated_at}.
GET /api/business -> {package:{id:'business-250',title,max_employees:250,mode:'pilot',price:0},workspace:Workspace|null}.
POST /api/business/activate {company_name} -> same envelope, idempotent.
POST /api/business/import/preview {filename,content_base64} -> {employees:EmployeeInput[],issues:[{row,field,message}],warnings:[{row,field,message}],row_count,valid:boolean}. No persistence.
POST /api/business/import {request_id,expected_revision,employees:EmployeeInput[]} -> {workspace:Workspace}.
PATCH /api/business/employees/{id} {expected_revision,employee:EmployeeInput} -> {workspace}.
POST /api/business/employees/{id}/remove {expected_revision} -> {workspace}; removes member references atomically.
POST /api/business/groups {expected_revision,group:GroupInput,id?:string} -> {workspace} (create/update).
POST /api/business/groups/{id}/remove {expected_revision} -> {workspace}.
GET /api/business/groups/{id}/report -> {report:GroupReport}.
GroupReport: {name,task,member_count,coverage:[{skill,employee_ids:string[]}],missing_skills:string[],available_hours:number|null,target_hours:number|null,missing_hours_data:string[],next_steps:string[],members:Employee[]}.
GET /api/business/template -> {filename:'numerom-business-template.csv',content:string} (UTF-8 BOM optional, semicolon CSV, Russian headers, one clearly fictional sample). No XLSX template dependency needed for first version; Excel opens this template and can save XLSX.
All non-activate endpoints require activated workspace. HTTP 409 for revision/import-key conflicts, 403 for absent access. Request parser's expected_revision is nonnegative integer and request_id bounded opaque id. Domain module exports EmployeeInput, GroupInput, parse_employee_file(filename:str,content:bytes)->dict, analyze_group(employees:list[dict],group:dict)->dict.
