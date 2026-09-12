"""
Take the machine configurations dict and the recipes.


Produce a recipe configurations which optimise for quality/s, quality/craft, total/craft, total/s

quality/craft
    quality disabled:
        all configs equivalent (0 quality output)

    quality enabled, productivity disabled:
        maximise quality

    quality enabled, productivity enabled:
        quality/productivity trade-off

quality/s
    quality disabled:
        all configs equivalent (0 quality output)

    quality enabled, productivity disabled:
        quality/speed trade-off

    quality enabled, productivity enabled:
        quality/productivity/speed trade-off

total/craft
    productivity disabled:
        all configs equivalent

    productivity enabled:
        maximise productivity

total/s
    productivity disabled:
        maximise speed

    productivity enabled:
        speed/productivity trade-off

"""
