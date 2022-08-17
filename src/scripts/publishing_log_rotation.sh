#!/usr/bin/env bash

PUBLOG_ROTATION_LOG=/logs/publishing_log_rotation.log

{
  echo "$(date): checking retention"
  python manage.py publishing_log -m retention
  echo "$(date): compressing rotated files"
  python manage.py publishing_log -m compress
} >> $PUBLOG_ROTATION_LOG
