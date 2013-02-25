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

def index(request):
	template = loader.get_template('GroupCraft/new_index.html')

	groups = Group.objects.all()
	if groups.__len__() > 5:
		groups = groups[0:5]

	tags = Tag.objects.all()
	sorted_tags = sorted(tags, key=lambda t: t.count)
	if sorted_tags.__len__() > 10:
		sorted_tags = sorted_tags[0:5]

	
	context = RequestContext(request, {'groups' : groups,'tags':sorted_tags})
	return HttpResponse(template.render(context))
		
def about(request):
	template = loader.get_template('GroupCraft/about.html')
	context = RequestContext(request, {})
	return HttpResponse(template.render(context))

@login_required
def group(request, group_name_url):
	template = loader.get_template('GroupCraft/group.html')

	groups = filter(
		lambda g: g.get_url() == group_name_url.lower(),
		Group.objects.all())

	context_dict = {}
	if groups:
		group = groups[0]
		usergroups = UserGroup.objects.filter(group = group)
		mem_names = []
		admin_names = []
		for ug in usergroups:
			if ug.isAdmin:
				admin_names.append(ug.user.user.username)
			else:
				mem_names.append(ug.user.user.username)

		context_dict = {'name':group.name,
		                'admins':admin_names,
		                'members':mem_names,
		                'url':group_name_url,
		                'valid':True}
	else:
		context_dict['name'] = Group.decode_group(group_name_url)
		context_dict['valid'] = False
		context_dict['url'] = group_name_url

	context = RequestContext(request, context_dict)
	return HttpResponse(template.render(context))

def user(request, username):
	template = loader.get_template('GroupCraft/user.html')
	data = {'username':username}

	user = User.objects.filter(username = username)

	if user:
		user = user[0]

	data['firstname'] = user.first_name
	data['lastname'] = user.last_name
	data['email'] = user.email

	context = RequestContext(request, {'data':data})
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
			tags = tag_string.split()
			for tag in tags:
				# if this is an existing tag, add one to the count
				old_tag = Tag.objects.filter(name=tag)
				if old_tag:
					old_tag = old_tag[0]
					old_tag.count += 1
					old_tag.save()
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
			return HttpResponseRedirect('/groupcraft/group/'+ Group.encode_group(g.name))
 		else:
			# the form contains errors,
			# show the form again, with error messages
			pass
	else:
		# a GET request was made, so we simply show a blank/empty form.
		form = GroupForm(initial = {'name':Group.decode_group(group_name)})

	# pass on the context, and the form data.
	return render_to_response('GroupCraft/add_group.html',
		{'form': form }, context)

@login_required
def join_group(request, group_name_url):

	context = RequestContext(request)
	template = loader.get_template('GroupCraft/join_group.html')

	context_dict = {}

	groups = Group.objects.filter(name = Group.decode_group(group_name_url))
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

@login_required
def search(request):
	context = RequestContext(request)
	result_list = []
	if request.method == 'POST':
		query = request.POST['query'].strip()
		if query:
			result_list = run_query(query)

	return render_to_response('GroupCraft/search.html',{ 'result_list': result_list }, context)