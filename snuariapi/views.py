from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from snuariapi.models import *
from snuariapi.serializers import *
from snuariapi.services import *

from config import domain

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        user = authenticate(username=username, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            response = Response({'id':user.id}, status=200)
            response['Set-Cookie'] = 'auth={}; HttpOnly; Domain={}; PATH=/'.format(token.key, domain)
            return response
        else:
            return Response('', status=400)

class LogoutView(APIView):
    def post(self, request):
        response = Response('', status=200)
        response['Set-Cookie'] = 'auth=; HttpOnly; Domain={}; PATH=/; Expires={}'.format(domain, 'Tue, 27 Nov 1990 22:31:29 GMT')
        return response

class SignupView(APIView):
    def post(self, request):
        password = request.data.get('password', None)
        if password is None or password is '':
            return Response('', status=400)

        email = request.data.get('email', None)
        if email is not None:
            if not email.endswith('@snu.ac.kr'):
                return Response('', status=400)

        user_serializer = UserSerializer(data=request.data)
        profile_serializer = ProfileSerializer(data=request.data)
        if user_serializer.is_valid() and profile_serializer.is_valid():
            user = user_serializer.save()
            profile_serializer = ProfileSerializer(user.profile, data=request.data)
            if profile_serializer.is_valid():
                profile_serializer.save()
                user.set_password(password)
                user.is_active = False
                user.save()

                # Set VerifyToken until there's no error
                while True:
                    try:
                        token = get_random_string(length=32)
                        vtoken = VerifyToken.objects.create(user=user, token=token)
                        send_verify_mail(token, user)
                        break
                    except:
                        continue

                return Response({'id':user.id})

        return Response('', status=400)

class VerifyView(APIView):
    def post(self, request):
        token = request.data.get('token', '')
        vtoken = VerifyToken.objects.filter(token=token).first()
        if vtoken is None:
            return Response('', status=400)

        vtoken.user.is_active = True
        vtoken.user.save()
        vtoken.delete()

        return Response('')
