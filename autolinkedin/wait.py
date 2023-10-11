from functools import partial

from seleniumtabs.wait import humanized_wait

humanized_wait = partial(humanized_wait, multiply_factor=3)
