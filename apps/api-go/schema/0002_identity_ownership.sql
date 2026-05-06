create table tenants (
    tenant_id varchar(64) primary key,
    display_name varchar(128) not null,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table users (
    user_id varchar(64) primary key,
    subject varchar(256) not null unique,
    display_name varchar(128) not null,
    token_fingerprint varchar(64),
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table tenant_memberships (
    tenant_id varchar(64) not null references tenants (tenant_id) on delete cascade,
    user_id varchar(64) not null references users (user_id) on delete cascade,
    role varchar(32) not null,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    primary key (tenant_id, user_id)
);

insert into tenants (
    tenant_id,
    display_name,
    created_at,
    updated_at
) values (
    'tenant_default',
    'Default Tenant',
    now(),
    now()
) on conflict (tenant_id) do nothing;

insert into users (
    user_id,
    subject,
    display_name,
    token_fingerprint,
    created_at,
    updated_at
) values (
    'user_legacy',
    'legacy-backfill',
    'Legacy Backfill',
    null,
    now(),
    now()
) on conflict (user_id) do nothing;

insert into tenant_memberships (
    tenant_id,
    user_id,
    role,
    created_at,
    updated_at
) values (
    'tenant_default',
    'user_legacy',
    'admin',
    now(),
    now()
) on conflict (tenant_id, user_id) do nothing;

alter table run_states
    add column tenant_id varchar(64),
    add column owner_user_id varchar(64),
    add column created_by_user_id varchar(64);

update run_states
set tenant_id = 'tenant_default',
    owner_user_id = 'user_legacy',
    created_by_user_id = 'user_legacy'
where tenant_id is null;

alter table run_states
    alter column tenant_id set not null,
    alter column owner_user_id set not null,
    alter column created_by_user_id set not null;

alter table run_states
    add constraint fk_run_states_tenant
        foreign key (tenant_id) references tenants (tenant_id),
    add constraint fk_run_states_owner_user
        foreign key (owner_user_id) references users (user_id),
    add constraint fk_run_states_created_by_user
        foreign key (created_by_user_id) references users (user_id);

create index ix_tenant_memberships_user_id on tenant_memberships (user_id);
create index ix_users_token_fingerprint on users (token_fingerprint);
create index ix_run_states_tenant_id on run_states (tenant_id);
create index ix_run_states_owner_user_id on run_states (owner_user_id);
create index ix_run_states_tenant_status on run_states (tenant_id, status);
create index ix_run_states_tenant_workflow_type on run_states (tenant_id, workflow_type);
