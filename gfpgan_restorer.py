import os
from gfpgan import GFPGANer


def restore(input_image, upscale=2, bg_upsampler=None):
    # model file path
    model_name = 'GFPGANCleanv1-NoCE-C2'
    model_path = os.path.join('gfpgan_model', model_name + '.pth')
    
    # set up GFPGAN restorer
    restorer = GFPGANer(
            model_path=model_path,
            upscale=upscale,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=bg_upsampler)
    
    # restore input_image
    _, _, restored_image = restorer.enhance(  input_image, 
                                        has_aligned=False, 
                                        only_center_face=False, 
                                        paste_back=True)
    
    return restored_image
