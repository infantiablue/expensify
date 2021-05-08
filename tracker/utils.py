from PIL import Image
import sys
from django.http import JsonResponse
from smartcrop import SmartCrop


def login_required_ajax(view_func, *args, **kwargs):
    from functools import wraps

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'You are not authorized.'})
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def crop_smart(inputfile, outputfile, img_height, img_width):
    image = Image.open(inputfile)
    # if image.mode != 'RGB' and image.mode != 'RGBA':
    #     sys.stderr.write("{1} convert from mode='{0}' to mode='RGB'\n".format(
    #         image.mode, inputfile))
    #     new_image = Image.new('RGB', image.size)
    #     new_image.paste(image)
    #     image = new_image

    cropper = SmartCrop()
    result = cropper.crop(image, width=100, height=int(
        img_height / img_width * 100))

    box = (
        result['top_crop']['x'],
        result['top_crop']['y'],
        result['top_crop']['width'] + result['top_crop']['x'],
        result['top_crop']['height'] + result['top_crop']['y']
    )
    # it should be an option to convert image to greyscale
    cropped_image = image.crop(box)
    cropped_image.thumbnail((img_width, img_height), Image.ANTIALIAS)
    cropped_image.save(outputfile, quality=100)
