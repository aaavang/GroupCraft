from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from groupcraft.search import run_query

from groupcraft.models import *

import os

def member_count(group):
	ugs = UserGroup.objects.filter(group = group)
	return ugs.__len__()

def index(request):
	template = loader.get_template('GroupCraft/new_index.html')

	featured= []
	for file in os.listdir("static/imgs/featured"):
		featured.append(file)

	groups = Group.objects.all()
	groups = sorted(groups, key=lambda g: member_count(g), reverse=True)
	if groups.__len__() > 5:
		groups = groups[0:5]

	tags = Tag.objects.all()
	tags = sorted(tags, key=lambda t: t.count)
	if tags.__len__() > 15:
		tags = tags[0:15]

	posts = []
	gc = Group.objects.filter(name = "GroupCraft")
	if gc:
		gc = gc[0]
		posts = Post.objects.filter(group = gc)
		posts = sorted(posts, key=lambda p: p.date, reverse=True)
		if posts.__len__() > 5:
			posts = posts[0:5]

	
	context = RequestContext(request, {'featured':featured,'groups' : groups,'tags':tags, 'posts':posts})
	return HttpResponse(template.render(context))
		
def about(request):
	template = loader.get_template('GroupCraft/about.html')
	context = RequestContext(request, {})
	return HttpResponse(template.render(context))


def group(request, group_name_url):
	template = loader.get_template('GroupCraft/group.html')

	groups = filter(
		lambda g: g.get_url() == group_name_url.lower(),
		Group.objects.all())

	context_dict = {}
	if groups:
		group = groups[0]
		usergroups = UserGroup.objects.filter(group = group)
		tgs = TagGroup.objects.filter(group = group)
		tags = []
		for tg in tgs:
			tags.append(tg.tag)

		mem_names = []
		admin_names = []
		for ug in usergroups:
			if ug.isAdmin:
				admin_names.append(ug.user.user.username)
			else:
				mem_names.append(ug.user.user.username)

		posts = Post.objects.filter(group=group)

		isMember = request.user.username in mem_names
		isAdmin = request.user.username in admin_names

		context_dict = {'name':group.name,
		                'admins':admin_names,
		                'members':mem_names,
		                'url':group_name_url,
		                'valid':True,
		                'tags':tags,
		                'posts':posts,
		                'isMember':isMember,
		                'isAdmin':isAdmin}
	else:
		context_dict['name'] = decode(group_name_url)
		context_dict['valid'] = False
		context_dict['url'] = group_name_url

	context = RequestContext(request, context_dict)
	return HttpResponse(template.render(context))

def user(request, username):
	template = loader.get_template('GroupCraft/user.html')
	context_dict = {'username':username}

	user = User.objects.get(username = username)
	if user:
		up = UserProfile.objects.get(user = user)
		ugs = UserGroup.objects.filter(user = user)
		groups = []

		for ug in ugs:
			groups.append(ug)

		context_dict['posts'] = Post.objects.filter(author = up)

		context_dict['firstname'] = user.first_name
		context_dict['lastname'] = user.last_name
		context_dict['email'] = user.email
		context_dict['groups'] = groups

	context = RequestContext(request, context_dict)
	return HttpResponse(template.render(context))


@login_required
def add_group(request,group_name):
	# immediately get the context - as it may contain posting data
	context = RequestContext(request)
	if request.method == 'POST':
		# data has been entered into the form via Post
		form = GroupForm(request.POST)
 		if form.is_valid():
			# the form has been correctly filled in,
			# so lets save the data to the model
			g = form.save(commit=True)
			# fetch the tags
			tag_string = form.cleaned_data['tags']
			tags = set(tag_string.split())
			for tag in tags:
				# if this is an existing tag, add one to the count
				t = Tag.objects.filter(name=tag)
				if t:
					t = t[0]
					t.count += 1
					t.save()
				else:
					# add the new tag
					t = Tag(name=tag,count = 1)
					t.save()
				# associate this tag with this group
				tg = TagGroup(tag = t, group = g)
				tg.save()
			u = User.objects.get(username = request.user)
			profile = UserProfile.objects.get(user = u)
			ug = UserGroup(user = profile,group = g, isAdmin = True)
			ug.save()
			# show the index page with the list of categories
			return HttpResponseRedirect('/groupcraft/group/'+ (g.get_url))
 		else:
			# the form contains errors,
			# show the form again, with error messages
			pass
	else:
		# a GET request was made, so we simply show a blank/empty form.
		form = GroupForm(initial = {'name':decode(group_name)})

	# pass on the context, and the form data.
	return render_to_response('GroupCraft/add_group.html',
		{'form': form }, context)

@login_required
def join_group(request, group_name_url):

	context = RequestContext(request)
	template = loader.get_template('GroupCraft/join_group.html')

	context_dict = {}

	groups = Group.objects.filter(name = decode(group_name_url))
	if groups:
		group = groups[0] #there can be only one...

		u = User.objects.get(username = request.user)
		profile = UserProfile.objects.get(user = u)

		# test to see if the user is already in this group
		ugs = UserGroup.objects.filter(group = group ).filter(user = profile)
		if ugs.__len__() == 0:
			ug = UserGroup(user = profile,group = group)
			ug.save()

		return HttpResponseRedirect('/groupcraft/group/'+ group_name_url)
	else:
		return HttpResponseRedirect('/groupcraft/')

def register(request):
	context = RequestContext(request)
	registered = False
	if request.method == 'POST':
		uform = UserForm(data = request.POST)
		pform = UserProfileForm(data = request.POST)
		if uform.is_valid() and pform.is_valid():
			user = uform.save()
			profile = pform.save(commit = False)
			profile.user = user
			profile.save()
			registered = True
			return index(request)
		else:
			print uform.errors, pform.errors
	else:
		uform = UserForm()
		pform = UserProfileForm()

	return render_to_response('GroupCraft/register.html', {'uform': uform, 'pform': pform, 'registered': registered }, context)


def user_login(request):
	context = RequestContext(request)
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				# Redirect to index page.
				return HttpResponseRedirect(request.POST['next'])
			else:
			# Return a 'disabled account' error message
				return HttpResponse("You're account is disabled.")
		else:
			# Return an 'invalid login' error message.
			print  "invalid login details " + username + " " + password
			return render_to_response('GroupCraft/login.html', {}, context)
	else:
		if(request.GET.has_key('next')):
			next_page = request.GET['next']
		else:
			next_page = '/groupcraft'
		# the login is a  GET request, so just show the user the login form.
		context = RequestContext(request, {'next':next_page})
		return render_to_response('GroupCraft/login.html', {} , context)
		
@login_required
def user_logout(request):
    context = RequestContext(request)
    logout(request)
    # Redirect back to index page.
    return HttpResponseRedirect('/groupcraft')


def search(request):
	context = RequestContext(request)
	context_dict = {}
	if request.method == 'POST':
		query = request.POST['query'].strip().lower()
		if query:
			context_dict['query'] = query
			query = query.split()
			tags = Tag.objects.all()
			groups = Group.objects.all()
			users = User.objects.all()
			tag_results = []
			group_results = []
			user_results = []
			for s in query:
				for t in tags:
					if s in t.name.lower():
						tag_results.append(t)
				for g in groups:
					if s in g.name.lower() or s in g.description.lower():
						group_results.append(g)
				for u in users:
					if s in u.username.lower():
						user_results.append(u)
			tag_results = set(tag_results)
			group_results = set(group_results)
			user_results = set(user_results)
			context_dict['tags'] = tag_results
			context_dict['users'] = user_results
			context_dict['groups'] = group_results

	return render_to_response('GroupCraft/new_search.html',context_dict, context)

def tag(request,tag_name):
	context = RequestContext(request)
	tag = filter(lambda t: t.name.lower() == tag_name,Tag.objects.all())
	context_dict = {};
	if tag:
		tag = tag[0]
		context_dict['name'] = tag.get_decoded()
		tgs = TagGroup.objects.filter(tag = tag)
		if tgs:
			groups = []
			for tg in tgs:
				groups.append(tg.group)
			context_dict['groups'] = groups
	else:
		context_dict['name'] = decode(tag_name)

	return render_to_response('GroupCraft/tag.html',context_dict,context)

def post(request,group_name_url):
	context = RequestContext(request)
	if request.method == 'POST':
		# it's sad that I had to resort to lambda functions...
		g =filter(
			lambda g: g.get_url() == group_name_url.lower(),
			Group.objects.all())
		g = g[0]
		u = User.objects.get(username = request.user)
		up = UserProfile.objects.get(user = u)

		text = request.POST['textarea'].strip()
		title = request.POST['title'].strip()
		p = Post(title=title,text=text,group=g,author=up)
		p.save()
		return group(request,group_name_url)

	else:
		return group(request,group_name_url)

