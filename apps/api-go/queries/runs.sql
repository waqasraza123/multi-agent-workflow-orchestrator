-- name: GetRunState :one
select
    run_id,
    tenant_id,
    owner_user_id,
    created_by_user_id,
    workflow_type,
    status,
    created_at,
    updated_at,
    payload
from run_states
where run_id = $1;

-- name: ListRunStates :many
select
    run_id,
    tenant_id,
    owner_user_id,
    created_by_user_id,
    workflow_type,
    status,
    created_at,
    updated_at,
    payload
from run_states
where ($3::text is null or tenant_id = $3)
order by created_at desc, run_id desc
limit $1 offset $2;

-- name: CreateRunState :exec
insert into run_states (
    run_id,
    tenant_id,
    owner_user_id,
    created_by_user_id,
    workflow_type,
    status,
    created_at,
    updated_at,
    payload
) values (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9
);
