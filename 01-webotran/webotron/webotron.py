#!/usr/bin/python .. which interpreter should use this script
# -*- coding: utf-8 -*- .. atom and Python3 use utf-8 coding by default

"""Webotron: Deploy websites with aws

Webotron automates the process of deploying static websites to aws.
- Configure AWS S3 list_buckets
    - Create them
    - Set them up for static website hosting
    - Deploy local files to them
As per Python guide, we shoud put import of pathlib and mimetypes on top
pathlib - for our code to be able to work on both windows and MAC
mimetypes - to guess the file extension(type)
boto3 - AWS Software Development Kit (SDK) for Python
"""
from pathlib import Path
import mimetypes
import boto3
from botocore.exceptions import ClientError
import click
# click is a cli creation kit, it's a Python package for cli
# To tell Boto3 to use the profile pythonAutomation, we create a session.
session = boto3.Session(profile_name='pythonAutomation')
"""To use resources, you invoke the resource() method of a Session
and pass in a service name"""
s3 = session.resource('s3')


@click.group()  # click.command () is a decorator.
# A decorator wraps the function.
# It will generate error messages, help messages for the function
# click.group() is another decorator, if we want our script
# to do more than one thing, use group.
def cli():
    "Webotron deploys websites to AWS"
    pass


@cli.command('list-buckets')
def list_buckets():  # our function
    """List all s3 buckets"""  # doc string
    for bucket in s3.buckets.all():  # to get a list of all buckets
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
# for the user to be able to pass the name of the bucket
# as an argument instead of hardcoding it in the script
def list_bucket_objects(bucket):
    """List objects in an s3 bucket"""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure S3 bucket"""

    s3_bucket = None

    try:
        s3_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint':
                                       session.region_name})
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
            # so get the bucket that I had created long back
        else:
            raise e


    """ Set the bucket Policy
     Triple quotes for the string to continue to the next line
    till the triple quotes end"""
    policy = """
        {
            "Version":"2012-10-17",
            "Statement":[{
            "Sid":"PublicReadGetObject",
            "Effect":"Allow",
            "Principal": "*",
                "Action":["s3:GetObject"],
                "Resource":["arn:aws:s3:::%s/*"
                ]
              }
            ]
         }
        """ % s3_bucket.name
    # the %s in Resource above will be replaced by s3_bucket.name
    policy = policy.strip()
    # to remove any blank space before and after the string

    pol = s3_bucket.Policy()
    # we get the policy object
    pol.put(Policy=policy)
    """ put function. Policy is the parameter name
    and policy is the policy we just created """

    ws = s3_bucket.Website()
    # we get the website object and use put function
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
                'Suffix': 'index.html'
        }
    })

    return


def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    # default text if mimetypes returns None (unable to guess)

    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': 'text/html'
                })


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET"""
    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()
    # we will get the absolute path of the directory

    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir():
                handle_directory(p)
            if p.is_file():
                upload_file(s3_bucket, str(p), str(p.relative_to(root)))

    handle_directory(root)


if __name__ == '__main__':
    cli()
