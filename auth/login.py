import json

from sejong_univ_auth import (ClassicSession, DosejongSession, MoodlerSession,
                              auth)


def lambda_handler(event, context):
    try:
        event = json.loads(event['body'])
        student_id = event['id']
        password = event['password']
        
        auth_data = auth(id=student_id, password=password, methods=[MoodlerSession, DosejongSession])
        return {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps({
                'name': auth_data.body['name'],
                'department': auth_data.body['major'],
                'grade': 1,
                'studentId': student_id,
                'year': int(student_id[:2])
            }, ensure_ascii=False)
        }
    except KeyError:
        return {
            "statusCode": 400,
            "headers": {},
            "body": json.dumps({
                'message': 'Invalid student_id or password',
            })
        }