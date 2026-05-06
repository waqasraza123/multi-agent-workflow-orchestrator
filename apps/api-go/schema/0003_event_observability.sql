alter table run_events
    add column request_id varchar(96) not null default '',
    add column traceparent varchar(128) not null default '';

create index ix_run_events_request_id on run_events (request_id);
create index ix_run_events_traceparent on run_events (traceparent);
