from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.http import urlquote, urlunquote
from django.utils.encoding import iri_to_uri


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
		return encode(self.name)



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

class Tag(models.Model):
	name = models.CharField(max_length=32,unique=True)
	count = models.PositiveIntegerField()

	def get_encoded(self):
		return encode(self.name)

	def get_decoded(self):
		return decode(self.name)

	def __unicode__(self):
		return self.name

class TagGroup(models.Model):
	group = models.ForeignKey(Group)
	tag = models.ForeignKey(Tag)

	def __unicode__(self):
		return self.group.name + self.tag.name

# create a form for Category and Page
class GroupForm(forms.ModelForm):
	tags = forms.CharField(max_length=50,
		help_text='Please enter the tags of the Group.')

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

def encode(string):
	# returns the name converted for insert into url
	encoded_string = string.replace(' ','_')
	encoded_string = encoded_string.lower()
	encoded_string = urlquote(encoded_string)
	return iri_to_uri(encoded_string)

def decode(string):
	# returns the category name given the category url portion
	decoded_string = urlunquote(string)
	decoded_string = decoded_string.replace('_',' ')

	return decoded_string


