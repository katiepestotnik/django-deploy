from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from .models import Cat, Toy, Photo
from .forms import FeedingForm
#sign up import
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
#add boto3 for photos from s3
import boto3
#globally unique strings
import uuid
#login to be able to hit routes
from django.contrib.auth.decorators import login_required

#authorize for class based views
from django.contrib.auth.mixins import LoginRequiredMixin

#constants s3
S3_BASE_URL = 'https://s3-us-west-1.amazonaws.com/'
BUCKET = 'katiescatcollector'

class CatCreate(LoginRequiredMixin,CreateView):
  model = Cat
  fields = ['name', 'breed', 'description', 'age']
  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class CatUpdate(LoginRequiredMixin, UpdateView):
  model = Cat
  fields = ['breed', 'description', 'age']

class CatDelete(LoginRequiredMixin,DeleteView):
  model = Cat
  success_url = '/cats/'

def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

@login_required
def cats_index(request):
  cats = Cat.objects.filter(user=request.user)
  return render(request, 'cats/index.html', { 'cats': cats })

@login_required
def cats_detail(request, cat_id):
  # look up how to only let the actual user for the cat to see this page
  #add user=request.user to objects.get()
  # add redirect if no cat but works, user can't see other cats by typing in url
  cat = Cat.objects.get(id=cat_id, user=request.user)
  # instantiate FeedingForm to be rendered in the template
  feeding_form = FeedingForm()
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
  print(toys_cat_doesnt_have)
  return render(request, 'cats/detail.html', {
    # pass the cat and feeding_form as context
    'cat': cat, 
    'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have
  })

@login_required
def add_feeding(request, cat_id):
	# create the ModelForm using the data in request.POST
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)

@login_required
def assoc_toy(request, cat_id, toy_id):
     Cat.objects.get(id=cat_id).toys.add(toy_id)
     return redirect('detail', cat_id=cat_id) 

@login_required
def add_photo(request, cat_id):
    #photo file will be the name attribute of the <input type='file'/> name used down on line 72 for key
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
          s3 = boto3.client('s3')
          print(f'this is s3: {s3}')
          #unique key for s3/needs image file extension
          key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
          print(f'this is key: {key}')
          #error handling
          try:
            s3.upload_fileobj(photo_file, BUCKET, key)
            # build full url string
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            print(f'this is url: {url}')
            # assign to cat_id
            photo=Photo(url=url, cat_id=cat_id)
            photo.save()
          except:
            print('An error occured uploading file to s3')       
    return redirect('detail', cat_id=cat_id)

def signup(request):
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'   
  form = UserCreationForm()
  context = {'form': form, 'error_message':error_message}
  return render(request, 'registration/signup.html', context)

class ToyList(LoginRequiredMixin, ListView):
  model = Toy

class ToyDetail(LoginRequiredMixin, DetailView):
  model = Toy

class ToyCreate(LoginRequiredMixin, CreateView):
  model = Toy
  fields = '__all__'

class ToyUpdate(LoginRequiredMixin,UpdateView):
  model = Toy
  fields = ['name', 'color']

class ToyDelete(LoginRequiredMixin,DeleteView):
  model = Toy
  success_url = '/toys/'