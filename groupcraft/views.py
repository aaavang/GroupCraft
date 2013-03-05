from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from groupcraft.models import *

import os

# helper function to determine membership size
def member_count(group):
	ugs = UserGroup.objects.filter(group = group)
	return ugs.__len__()

# this view is called when a user wants to view the homepage
def index(request):
	template = loader.get_template('GroupCraft/new_index.html')

	# fetch the featured images
	featured= []
	for file in os.listdir("static/imgs/featured"):
		featured.append(file)

	# fetch the 5 largest groups
	groups = Group.objects.all()
	groups = sorted(groups, key=lambda g: member_count(g), reverse=True)
	if groups.__len__() > 5:
		groups = groups[0:5]

	# select the 15 most popular tags
	tags = Tag.objects.all()
	tags = sorted(tags, key=lambda t: t.count)
	if tags.__len__() > 10:
		tags = tags[0:10]

	# select the newest 5 posts from the GroupCraft group
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

# this view is called when a user wants to view the about page
def about(request):
	template = loader.get_template('GroupCraft/about.html')
	context = RequestContext(request, {})
	return HttpResponse(template.render(context))

# this view is called when a user wants to view a group page
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
		tag_string = ''
		for tag in tags:
			tag_string += tag.name + " "

		context_dict = {'name':group.name,
		                'desc':group.description,
		                'tag_string':tag_string,
		                'admins':admin_names,
		                'members':mem_names,
		                'url':group_name_url,
		                'valid':True,
		                'isPrivate':group.isPrivate,
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

# this view is called when a user wants to view a user page
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

		context_dict['posts'] = sorted(Post.objects.filter(author = up),key= lambda p: p.date,reverse=True)

		context_dict['firstname'] = user.first_name
		context_dict['lastname'] = user.last_name
		context_dict['email'] = user.email
		context_dict['groups'] = groups
		context_dict['isUser'] = request.user == user

	context = RequestContext(request, context_dict)
	return HttpResponse(template.render(context))

# this view is called when a user wants to create a group by filling out the group
# form
def create_tags(g, tag_string):
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
			t = Tag(name=tag, count=1)
			t.save()
		# associate this tag with this group
		tg = TagGroup(tag=t, group=g)
		tg.save()


@login_required
def add_group(request):
	# immediately get the context - as it may contain posting data
	context = RequestContext(request)

	# only do something if this came from the register modal form
	if request.method == 'POST':
		# data has been entered into the form via Post
		form = GroupForm(request.POST)
		if form.is_valid():
			# the form has been correctly filled in,
			# so lets save the data to the model
			g = form.save(commit=True)
			# fetch the tags
			if 'tags' in form.cleaned_data.keys():
				tag_string = form.cleaned_data['tags']
				create_tags(g, tag_string)
			u = User.objects.get(username = request.user)
			profile = UserProfile.objects.get(user = u)
			ug = UserGroup(user = profile,group = g, isAdmin = True)
			ug.save()
			# show the newly created group page
			return HttpResponseRedirect('/groupcraft/group/'+ g.get_url())
		else:
			# the form contains errors,
			# show the form again, with error messages
			pass
	else:
		pass

	# pass on the context
	return HttpResponseRedirect('/groupcraft/')

@login_required
def edit_group(request):
	if request.method == 'POST':
		old_name = request.POST['old_name']
		g = Group.objects.get(name = old_name)
		g.name = request.POST['name']
		g.description = request.POST['description']
		g.save()
		tags = TagGroup.objects.filter(group = g)
		for tag in tags:
			tag.tag.count -= 1
			tag.tag.save()
		tags.delete()
		create_tags(g, request.POST['tags'])
		return HttpResponseRedirect('/groupcraft/group/'+g.get_url())
	else:
		return HttpResponseRedirect('/groupcraft/')

# this view is called when a user wants to join a group
@login_required
def join_group(request, group_name_url):

	groups = filter(
		lambda g: g.get_url() == group_name_url.lower(),
		Group.objects.all())
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
		return HttpResponseRedirect('/groupcraft/'+ group_name_url)

# this view is called when a user submits the register form
def register(request):
	context = RequestContext(request)
	registered = False

	# only do something if this came from the form
	if request.method == 'POST':
		uform = UserForm(data = request.POST)
		pform = UserProfileForm(data = request.POST)
		if uform.is_valid() and pform.is_valid():
			user = uform.save()
			# form brings back a plain text string, not an encrypted password
			pw = user.password
			# thus we need to use set password to encrypt the password string
			user.set_password(pw)
			user.save()
			profile = pform.save(commit = False)
			profile.user = user
			profile.save()
			registered = True
		else:
			print uform.errors, pform.errors
	else:
		pass

	return HttpResponseRedirect(request.environ['HTTP_REFERER'])

# this view is called when the user submits the login form
def user_login(request):
	context = RequestContext(request)

	# only do something if this comes from the login modal form
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				# Redirect to current page.
				return HttpResponseRedirect(request.environ['HTTP_REFERER'])
			else:
			# Return a 'disabled account' error message
				return HttpResponse("You're account is disabled.")
		else:
			# Return an 'invalid login' error message.
			print  "invalid login details " + username + " " + password
			return HttpResponseRedirect(request.environ['HTTP_REFERER'])
	else:
		return HttpResponseRedirect('/groupcraft/')

# this view is called when the user wants to logout
@login_required
def user_logout(request):
	context = RequestContext(request)
	logout(request)
	# Redirect back to index page.
	return HttpResponseRedirect('/groupcraft')

# this view is called when the user uses the search box
def search(request):
	context = RequestContext(request)
	context_dict = {}

	# only do something if this came from the search box
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

			# for each query string, perform a search
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

			# store the results
			tag_results = set(tag_results)
			group_results = set(group_results)
			user_results = set(user_results)
			context_dict['tags'] = tag_results
			context_dict['users'] = user_results
			context_dict['groups'] = group_results

	return render_to_response('GroupCraft/new_search.html',context_dict, context)

# this view is called when the user clicks on a tag
def tag(request,tag_name):
	context = RequestContext(request)
	tag = filter(lambda t: t.name.lower() == tag_name,Tag.objects.all())
	context_dict = {}
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

# this view is called to add a post to a group
def post(request,group_name_url):
	context = RequestContext(request)

	# we only do something if this came from the form
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

# this view is called to remove a user from a group
def remove(request,username,group_name_url):
	g =filter(
		lambda g: g.get_url() == group_name_url.lower(),
		Group.objects.all())

	# if the group exists...
	if g:
		g = g[0]
		u_requester = User.objects.filter(username = request.user)
		u_delete = User.objects.filter(username = username)

		# if the users in question exist...
		if u_requester and u_delete:
			u_requester = u_requester[0]
			u_delete = u_delete[0]
			ug_requester = UserGroup.objects.filter(user = u_requester).filter(group = g)
			ug_delete = UserGroup.objects.filter(user = u_delete).filter(group = g)

			# if the users are members of this group...
			if ug_requester and ug_delete:
				ug_requester = ug_requester[0]

				# if the requester has the authority to delete a user...
				if ug_requester.isAdmin:
					# delete the user group associated with the user/group
					ug_delete.delete()
				else:
					pass
		else:
			pass
	else:
		pass

	# redirect the user to the group page in question
	return HttpResponseRedirect('/groupcraft/group/' + group_name_url)

