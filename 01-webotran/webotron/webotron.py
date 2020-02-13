import boto3
import click
from botocore.exceptions import ClientError

#To tell Boto3 to use the profile pythonAutomation, we create a session.
session = boto3.Session(profile_name='pythonAutomation')
#To use resources, you invoke the resource() method of a Session and pass in a service name
s3 = session.resource('s3')
# click is a cli creation kit, it's a Python package for cli
@click.group() ##click.command () is a decorator.
#A decorator wraps the function.
#It will generate error messages, help messages for the function
#click.group() is another decorator, if we want our script
#to do more than one thing, use group.
def cli():
    "Webotron deploys websites to AWS"
    pass
@cli.command('list-buckets')
def list_buckets(): # our function
    "List all s3 buckets" #doc string
    for bucket in s3.buckets.all(): #to get a list of all buckets
        print(bucket)

@cli.command('list-bucket-objects')
@click.argument('bucket') # for the user to be able to pass the name of the bucket as an argument instead of hardcoding it in the script
def list_bucket_objects(bucket):
    "List objects in an s3 bucket"
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)

@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    "Create and configure S3 bucket"
    s3_bucket = None

    try:
        s3_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': session.region_name}
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise e

# Set the bucket Policy
#triple quotes for the string to continue to the next line till the triple quotes end
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
    policy = policy.strip() #to remove any blank space before and after the string

    pol = s3_bucket.Policy() #we get the policy object
    pol.put(Policy=policy) #put function. Policy is the parameter name and policy is the policy we just created


    ws = s3_bucket.Website() # we get the website object and use put function
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })

    return





if __name__ == '__main__':
    cli()
