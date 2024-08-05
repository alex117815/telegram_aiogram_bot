from decouple import config

async def get_admins():
    print([int(admin_id) for admin_id in config('ADMINS').split(',')])
    return [int(admin_id) for admin_id in config('ADMINS').split(',')]