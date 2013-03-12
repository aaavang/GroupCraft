import os

def  css_processor(request):
	CSS = os.environ['CSS']

	try:
		return {'CSS': CSS}
	except NameError:
		CSS = 'zurb'
		return {'CSS': CSS}
