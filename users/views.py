from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction, Task
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.utils import timezone
from .serializers import UserSerializer, TransactionSerializer, TaskSerializer
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from IPython.display import display
from prophet import Prophet
from django.contrib.auth.tokens import default_token_generator
from users.utils import send_verif_up_mail, resset_pass_mail
from django.utils.http import urlsafe_base64_decode
#------------Auth------------
@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username']) #получаем обьект юзер(где юзернейм = реквест юзернейм) или поднимаем 404 
    if not user.check_password(request.data['password']):
        return Response({'detail': 'Not found.'}, status = status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user) #присваиваем/даем токен юзера 
    serializer = UserSerializer(instance=user) 
    return Response({'token': token.key, 'user': serializer.data}) 

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data = request.data) #аналог формы 
    if serializer.is_valid():
        serializer.save() #сохраняем в бд
        user = User.objects.get(username = request.data['username']) #получаем этого же пользователя
        user.set_password(request.data['password']) #устанавливаем пароль в хеш-формате
        user.save() #сохраняем пользователя
        send_verif_up_mail(request,user)
        #token = Token.objects.create(user=user) #создаем токен для юзера
        return Response('confirm your email',status=status.HTTP_102_PROCESSING)
        #return Response({'token': token.key, 'user': serializer.data})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def mailconfirm(request,uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return Response('email confirmed')
    else:
        return Response('smth went wrong')

@api_view(['POST'])
def wannaresetpass(request):
    email = request.data['email']
    user = User.objects.get(email = email)
    resset_pass_mail(email, user)
@api_view(['POST'])
def resetpassword(request, token, uidb64): 
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        newpass = request.data.get('new_password')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(status=status.HTTP_400_BAD_REQUEST)
    user.set_password(newpass)
    user.save()
    return Response('password changed', status=status.HTTP_200_OK)

#-------------Transactions--------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction(request):
    #распаковываем реквест по человечески 
    user = request.user
    category = request.data.get('category')
    start_amount = request.data.get('start_amount')
    end_amount = request.data.get('end_amount')
    start_time = request.data.get('start_time')
    end_time = request.data.get('end_time')
    currency =request.data.get('currency')
    
    filters = {'user': request.user} #создаем список(словарь) фильтров а потом если if  то закидываем в список фильтр
    
    if category:
        filters['category'] = category  
    if start_amount:
        filters['amount__gte'] = start_amount  
    if end_amount:
        filters['amount__lte'] =  end_amount
    if start_time:
        filters['time__gte'] = start_time 
    if end_time:
        filters['time__lte'] = end_time
    if currency:
        filters['currency'] = currency

    transaction = Transaction.objects.filter(**filters) #**filters это словарь который делается выше
    serializer = TransactionSerializer(transaction, many = True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_transaction(request):
    
    #данные на валидацию которые точно не могут быть пустыми
    validate = {
        'category': request.data.get('category', ''),
        'amount': request.data.get('amount'),
        'currency': request.data.get('currency'),
    }
    serializer = TransactionSerializer(data = validate)
    
    #time validator/cleaner
    if request.data['time'] == '':
        cleaned_time = timezone.now()
    else:
        cleaned_time = request.data['time']
    
    #category validator/cleaner
    if request.data['category'] == '':
        cleaned_category = 'others'
    else:
        cleaned_category = request.data['category'] 
    try:
        if serializer.is_valid():
            
            Transaction.objects.create(
                user = request.user,
                category = cleaned_category,
                amount = request.data['amount'],
                time = cleaned_time,
                description = request.data['description'],
                currency = request.data['currency'],
            )
        return Response({"message": "Transaction added correctly"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print("Error:", str(e))
        return Response("An error occurred. Transaction not added.")
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_transaction(request):
    try:
        filters = {
            'id': request.data['id'],
            'user_id': request.user
        }
        
        transaction_to_delete = Transaction.objects.filter(**filters)
        transaction_to_delete.delete()
        return Response('delete', status=status.HTTP_200_OK)
    except:
        return Response('something went wrong with updating task', status=status.HTTP_400_BAD_REQUEST)        


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sort_by_category(request): # получить все транзакции по одной категории

    filters = {                                  
        'user': request.user,
        'category': request.data.get('category')
        } 
    queryset = Transaction.objects.filter(**filters)
    df = pd.DataFrame.from_records(queryset.values())
    context = df.to_json(orient='records')
    return Response(context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def procent_of_categories(request):  # получить в процентах транзакции(можно на какой то период времени(наверное но я не тестил начсет периода))
    
    start_time = request.data.get('start_time')
    end_time = request.data.get('end_time')
    
    filters = {'user': request.user}
    
    if start_time:
        filters['time__gte'] = start_time 
    if end_time:
        filters['time__lte'] = end_time
    
    queryset = Transaction.objects.filter(**filters)
    df = pd.DataFrame.from_records(queryset.values())
    total_rows = len(df)
    category_counts = df['category'].value_counts()
    percentage_by_category = (category_counts / total_rows) * 100
    category_counts_dict = percentage_by_category.to_dict()
    return Response(category_counts_dict)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])    
def month_transaction_info(request):
    start_date = datetime.strptime(request.data.get('time'), '%Y-%m')
    end_date = start_date + relativedelta(months=+1)
    filters = {
        'user': request.user,
        'time__gte': start_date,
        'time__lte': end_date
    }
    queryset = Transaction.objects.filter(**filters)
    df = pd.DataFrame.from_records(queryset.values())
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    middle_transaction = df['amount'].mean()
    highest_expense = df['amount'].min()
    highest_income = df['amount'].max()
    total_expense = df[df['amount'] < 0]['amount'].sum()
    
    #display(df)
    
    total_income = df[df['amount']>0]['amount'].sum()

    total_left = total_income - total_expense
    def category_stat(): 
        total_rows = len(df)
        category_counts = df['category'].value_counts()
        percentage_by_category = (category_counts / total_rows) * 100
        category_dict = percentage_by_category.to_dict()
        return category_dict
    
    
    context={
        'middle_transaction': middle_transaction,
        'highest_expense': highest_expense,
        'highest_income': highest_income,
        'total_expense': total_expense,
        'total_income': total_income,
        'total_left': total_left,
        'category_stat': category_stat()
    }    
    return Response(context)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forecast_transaction(request):
    
    try:
        filters = {
            'user': request.user,
            'time__lte': timezone.now()
        }
        queryset = Transaction.objects.filter(**filters)
    except:
        return Response('probably,user havent any transactions',status=status.HTTP_404_NOT_FOUND)

    df = pd.DataFrame.from_records(queryset.values())
    df['time'] = pd.to_datetime(df['time']).dt.tz_localize(None) #конвертируем время в дататайм тип и убираем utc
    df = df.sort_values(by = 'time') #перебераем по дате транзакции и упорядочиваем
    
    for i in range(1, len(df)):                #суммируем каждую транзакцию i с i-1
        df.loc[i, 'amount'] = df.loc[i, 'amount'] + df.loc[i - 1, 'amount']
    display(df)
    data_ph = {'ds': df['time'], 'y': df['amount'], 'r0': df['category']}#создаем данные для датафрейма дата/транзакция/category
    
    
    df_ph = pd.DataFrame(data_ph)                   #создаем датафрейм дата/транзакция/категория
    
    model = Prophet(daily_seasonality = False, weekly_seasonality = False, yearly_seasonality = False, changepoint_prior_scale=0.000003, seasonality_prior_scale=5 ) #создаем модель и задаем параметры
    model.add_seasonality(name = 'monthly', period=30.5, fourier_order=7)
    model.add_country_holidays(country_name= 'PL')
    model.fit(df_ph) 
    future = model.make_future_dataframe(periods=30) #создаем дф на котором будем делать прогноз(количество дней)
    forecast = model.predict(future) #создаем дф с предиктом = предсказываем че спрогнозировали
    print('==========================================FORECASST=============================')
    display(forecast) #отображаем в консоли предикт
    model.plot(forecast) #рисуем график предикта
    plt.show() #показываем граф предикта
    comp = model.plot_components(forecast) #компоненты (неделя тренд год) 
    print('==========================================COMPONENTSSSSSSSSSS=========================')
    display(comp) #выводим в консоль
    plt.show() #рисуем
    #seasonally_data = forecast[['ds', 'weekly']] #ПОМЕТКААААААА дописать ретерн недельного тренда
    plt.show()
    returns_front = forecast[['ds', 'yhat']]
    display(returns_front)
    #forecast = pd.DataFrame.to_json(forecast)
    #seasonally_data = pd.DataFrame.to_json(seasonally_data)
    returns_front = returns_front.to_json()
    print('=====================================================================returns_to_front============================================')
    display(returns_front)
    context =  {
        returns_front
    }   
    
    return Response(context, status=status.HTTP_200_OK)

#------------To-Do-List------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_task(request):
    serializer = TaskSerializer(data=request.data)
    if 'deadline' not in request.data or request.data['deadline'] == '':
        cleaned_deadline = timezone.now() + relativedelta(days=+1)
    else:
        cleaned_deadline = request.data['deadline']
    try:
        Task.objects.create(
            user = request.user,
            title = request.data['title'],
            description = request.data['description'],
            deadline = cleaned_deadline
            )
        return Response('valid', status=status.HTTP_200_OK)
    except:
        return Response('something went wrong,transaction was not added', status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_task(request):
    try:
        filters = {
            'id': request.data['id'],
            'user_id': request.user
        }
        
        task_to_update = Task.objects.filter(**filters)
        task_to_update.update(complete = request.data['complete'])
        return Response('updated', status=status.HTTP_200_OK)
    except:
        return Response('something went wrong with updating task', status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task(request):
    filters = {'user': request.user}
    task = Task.objects.filter(**filters)
    serializer = TaskSerializer(task, many=True)
    return Response(serializer.data)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_task(request):
    try:
        filters = {
            'id': request.data['id'],
            'user_id': request.user
        }
        
        task_to_delete = Task.objects.filter(**filters)
        task_to_delete.delete()
        return Response('delete', status=status.HTTP_200_OK)
    except:
        return Response('something went wrong with updating task', status=status.HTTP_400_BAD_REQUEST)        
    