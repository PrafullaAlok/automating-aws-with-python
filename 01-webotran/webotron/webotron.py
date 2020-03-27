#!/usr/bin/python .. which interpreter should use this script
# -*- coding: utf-8 -*- .. atom and Python3 use utf-8 coding by default

"""Webotron: Deploy websites with aws

Webotron automates the process of deploying static websites to aws.
- Configure AWS S3 list_buckets
    - Create them
    - Set them up for static website hosting
    - Deploy local files to them

boto3 - AWS Software Development Kit (SDK) for Python
"""

import boto3
import click
# click is a cli creation kit, it's a Python package for cli

from bucket import BucketManager

session = None
bucket_manager = None

@click.group()  # click.command () is a decorator.
# A decorator wraps the function.
# It will generate error messages, help messages for the function
# click.group() is another decorator, if we want our script
# to do more than one thing, use group.
@click.option('--profile', default=None,
    help="Use a given AWS profile.")
def cli(profile):
    "Webotron deploys websites to AWS"
    global session, bucket_manager
    session_cfg = {}  # session config dictionary
    if profile:
        session_cfg['profile_name'] = profile

    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)


@cli.command('list-buckets')
def list_buckets():
    """List all s3 buckets"""  # doc string
    for bucket in bucket_manager.all_buckets():  # to get a list of all buckets
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
# for the user to be able to pass the name of the bucket
# as an argument instead of hardcoding it in the script
def list_bucket_objects(bucket):
    """List objects in an s3 bucket"""
    for obj in bucket_manager.all_objects(bucket):
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure S3 bucket"""
    s3_bucket = bucket_manager.init_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)

    return


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET"""
    bucket_manager.sync(pathname, bucket)


if __name__ == '__main__':
    cli()
