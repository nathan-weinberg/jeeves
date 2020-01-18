from main import *

def test_percent_func():
	assert percent(0, 1) == 0.0
	assert percent(1, 2) == 50.0
	assert percent(1, 1) == 100.0
