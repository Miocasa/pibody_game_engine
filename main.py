from engine import demo
demo.run()

# from engine import iotest
# iotest.run()

# from engine import st7789

# drv = st7789()
# drv.draw_image("demo/module_pngs/motion_sensor.png", 0,0)



# import os

# def tree(path="/", level=0):
#     try:
#         for f in os.listdir(path):
#             print("  " * level + f)
#             p = path.rstrip("/") + "/" + f
#             try:
#                 os.listdir(p)
#                 tree(p, level + 1)
#             except:
#                 pass
#     except Exception as e:
#         print(e)

# tree("/")