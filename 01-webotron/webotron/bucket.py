# -*- coding: utf-8 -*-
""" pathlib - for our code to be able to work on both windows and MAC
    mimetypes - to guess the file extension(type)"""

"""Classes for S3 Buckets."""

import mimetypes
from pathlib import Path
import util
from botocore.exceptions import ClientError


class BucketManager:
    """Manage an S3 Bucket."""

    def __init__(self, session):
        """Create a BucketManager object.
        To use resources, you invoke the resource() method of a Session
        and pass in a service name"""
        self.session = session
        self.s3 = self.session.resource('s3')

    def get_region_name(self, bucket):
        """Get the bucket's region name."""
        client = self.s3.meta.client
        bucket_location = client.get_bucket_location(Bucket=bucket.name)

        return bucket_location["LocationConstraint"] or 'us-east-1'

    def get_bucket_url(self, bucket):
        """Get the website URL for this bucket."""
        return "http://{}.{}".format(bucket.name,
                        util.get_endpoint(self.get_region_name(bucket)).host
                        )

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get an iterator for all objects in bucket"""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):
        """Create a new bucket or return existing one by name."""
        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.session.region_name
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
                # so get the bucket that I had created long back
            else:
                raise e

        return s3_bucket

    def set_policy(self, bucket):
        """Set the bucket Policy to be readable by everyone"""
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
            """ % bucket.name
        # the %s in Resource above will be replaced by s3_bucket.name
        policy = policy.strip()
        # to remove any blank space before and after the string
        pol = bucket.Policy()
        # we get the policy object
        pol.put(Policy=policy)
        """ put function. Policy is the parameter name
        and policy is the policy we just created """

    def configure_website(self, bucket):
        """Configure s3 website hosting for Bucket."""
        # we get the website object and use put function
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                    'Suffix': 'index.html'
            }
        })

    @staticmethod
    def upload_file(bucket, path, key):
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        # default text if mimetypes returns None (unable to guess)

        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': 'text/html'
            })

    def sync(self, pathname, bucket_name):
        """Sync contents of path to bucket."""
        bucket = self.s3.Bucket(bucket_name)
        root = Path(pathname).expanduser().resolve()
        # resolve will give the absolute path of the directory

        def handle_directory(target):
            for p in target.iterdir():  # iterate over the directory
                # If p is a directory, iterate over, if it's a file, upload it
                if p.is_dir():
                    handle_directory(p)  # recursion
                if p.is_file():
                    self.upload_file(bucket, str(p), str(p.relative_to(root)))

        handle_directory(root)
