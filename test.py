import hashlib

def generate_md5_hash(input_string):
    print(input_string)
    # Create an MD5 hash object
    md5_hash = hashlib.md5()

    # Encode the string to bytes and update the hash object
    md5_hash.update(input_string.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    return md5_hash.hexdigest()


print (generate_md5_hash('https://sjobs.brassring.com/TGnewUI/Search/Home/Home?partnerid=26209&siteid=5179&jobid=1361567'))
print ("*"*60)
print (generate_md5_hash('https://sjobs.brassring.com/TGnewUI/Search/Home/Home?partnerid=26209&siteid=5179&jobid=1361567#jobDetails=1361567_5179'))