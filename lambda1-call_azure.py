import json
import urllib.parse
import boto3
import requests
import traceback
import os
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        azure_cv_key = os.environ.get('azure_cv_key')

        #S3 트리거로부터 버킷 이름, 키를 가져옴
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        print(f"object: {key}, bucket: {bucket}")
        
        try:
            #해당 버킷의 키를 저장
            response = s3.get_object(Bucket=bucket, Key=key)

        except Exception as s3_error:
            print(f"S3 Get Object Error: {s3_error}")
            print(traceback.format_exc())
            raise
        
        # s3.get_object에서 반환한 값은 Body에 있는데 이걸 image_data 변수에 저장
        # 이 버킷에는 이미지만 저장됨
        image_data = response['Body'].read()
        
        # Azure의 computer vision 엔드포인트
        base_url = "https://test-instance-1205.cognitiveservices.azure.com"

        #문서의 featuer 참고: https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/how-to/call-analyze-image-40?tabs=csharp&pivots=programming-language-rest-api
        #caption: describe image -> 한국어 지원하지 않음
        #read: read readable text
        #tags: labeling image
        api_url = f"{base_url}/computervision/imageanalysis:analyze?features=caption,tags&model-version=latest&language=en&api-version=2024-02-01"
        
        #헤더 정보
        headers = {
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': azure_cv_key
        }
        
        # api로 이미지 전송
        try:
            api_response = requests.post(api_url, headers=headers, data=image_data)
            
            # HTTP 코드 확인, 200이 아니라면 에러를 발생시킴
            if api_response.status_code != 200:
                print(f"API Error: {api_response.status_code}")
                print(f"API Response: {api_response.text}")
                raise Exception(f"API request failed with status {api_response.status_code}")
            
            # API 응답 로깅
            print(f"API Response: {api_response.status_code}")
            print(f"API Response Body: {api_response.text}")

            #json 형식으로 반환
            api_response_data = api_response.json()
            print(f"API Response in JSON: {api_response_data}")

            # 여기서 분기해야 함. text인 경우와 그렇지 않은 경우로 분기
            # text인 경우 OCR API를 호출
            for item in api_response_data['tagsResult']['values']:
                print('log1 : ', item)  # 전체 항목 출력
                print('log1 name: ', item.get("name"))
                print('log1 confidence: ', item.get("confidence"))
    
                if item.get("name") == "text" and item.get("confidence", 0) >= 0.9:
                    print('log2 : 조건 만족')
                    # OCR API 호출 로직
                    api_url = f"{base_url}/computervision/imageanalysis:analyze?features=read&model-version=latest&language=en&api-version=2024-02-01"
                    api_response = requests.post(api_url, headers=headers, data=image_data)
        
                    # API 응답 로깅
                    print(f"API Response in OCR: {api_response.status_code}")
                    print(f"API Response Body in OCR: {api_response.text}")
                    


                    #OCR 응답 중 유의미한 부분을 리스트로 만들어 반환
                    api_response_data = api_response.json() #json으로 처리하기 위함
                    result_list = []
                    result_list.append(api_response_data['captionResult']['text'])

                    ocr = [api_response_data['readResult']['blocks']['lines']['text']] #사진의 텍스트 값

                    result_list.append(ocr)
                    print('result_list: ', reuslt_list)

                    return {
                        'statusCode': 200,
                        'body': json.dumps('Image processed and sent to API successfully!')
                    }

            #text가 없다면 기존 api 응답을 반환
            result_list = []
            result_list.append(api_response_data['captionResult']['text'])
            tmp_list = []
            for item in api_response_data['tagsResult']['values']:
                if item['confidence'] > 0.85:
                    tmp_list.append(item['name'])
            
            result_list.append(tmp_list)
            print('result_list: ', reuslt_list)

            return {
                    'statusCode': 200,
                    'body': json.dumps('Image processed and sent to API successfully!')
            }
        
        except requests.RequestException as req_error:
            print(f"Request Error: {req_error}")
            print(traceback.format_exc())
            raise
        
    except Exception as e:
        print(f"General Error: {e}")
        print(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing image: {str(e)}')
        }
