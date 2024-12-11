import json
import boto3
import datetime

# Initialize the S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        bucket_name = 'test-kilolog'

        #body에서 user_id, date, file_name을 받아야 함
        body = json.loads(event['body']) if event.get('body') else {}

        user_id = body.get('user_id')  
        date = body.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
        file_name = body.get('file_name', datetime.datetime.now().strftime('%Y-%m-%d'))
        
        #s3 키 생성
        s3_key = f"{user_id}/{date}/{file_name}"

        # s3에 빈 오브젝트 삽입. S3 키를 생성하기 위함임
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_name  # Empty body to create a "directory"
        )

        print(f"log1 | Bucket: {bucket_name}, Key: {s3_key}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Directory structure created successfully!',
                'bucket_name': bucket_name,
                's3_key': s3_key
            })
        }

    except ValueError as ve:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid input',
                'error': str(ve)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error occurred',
                'error': str(e)
            })
        }

