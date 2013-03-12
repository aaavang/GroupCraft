import os

def  css_processor(request):
	CSS = os.environ['CSS']

	try:
		if CSS == 'zurb':
			return {'CSS': CSS, 'NIGHT':False}
		else:
			return {'CSS': CSS, 'NIGHT':True}
	except NameError:
		CSS = 'zurb'
		return {'CSS': CSS, 'NIGHT':False}
