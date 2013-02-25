from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
import urllib

class UserProfile(models.Model):
	# This field is required.
	user = models.OneToOneField(User)
	# These fields are optional
	website = models.URLField(blank=True)
	picture = models.ImageField(upload_to='imgs', blank=True)

	def __unicode__(self):
		return self.user.username

class Group(models.Model):
	name = models.CharField(max_length=128,unique=True)
	description = models.TextField(max_length=512)

	def get_url(self):
		return self.encode_group(self.name)

	@staticmethod
	def encode_group(group_name):
		# returns the name converted for insert into url
		encoded_name = group_name.replace(' ','_')
		encoded_name = encoded_name.lower()
		encoded_name = urllib.quote(encoded_name)
		return encoded_name

	@staticmethod
	#TODO FIX THIS.  It is very inefficient
	def decode_group(group_url):
		# returns the category name given the category url portion
		decoded_name = urllib.unquote(group_url)
		decoded_name = group_url.replace('_',' ')

		return decoded_name

	def __unicode__(self):
		return self.name

class Post(models.Model):
	date = models.DateTimeField(auto_now_add=True)
	title = models.CharField(max_length=128)
	text = models.TextField()
	author = models.ForeignKey(UserProfile)
	group = models.ForeignKey(Group)
	replyTo = models.ForeignKey('self')

	def __unicode__(self):
		return self.title

class UserGroup(models.Model):
	user = models.ForeignKey(UserProfile)
	group = models.ForeignKey(Group)
	isAdmin = models.BooleanField()

	def __unicode__(self):
		return self.user.user.username + self.group.name

# create a form for Category and Page
class GroupForm(forms.ModelForm):
	name = forms.CharField(max_length=50,
		help_text='Please enter the name of the Group.')

	class Meta:
		# associate the model, Group, with the ModelForm
		model = Group

class UserForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ["username", "email", "password"]

class UserProfileForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		fields = ["website","picture"]


