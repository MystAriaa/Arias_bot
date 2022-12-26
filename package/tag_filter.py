from datetime import datetime, timezone

def extract_tag(reason,time):

    permanent=0 
    timeout=0 
    commented=0 
    notcommented=0 
    sexism=0 
    homophobia=0 
    rascism=0 
    backseat=0
    spam=0 
    username=0
    other=0 

    if (time == ""):
        permanent = 1
    else:
        timeout = 1
    if (reason == ""):
        notcommented = 1
    else:
        commented = 1
    if ("sex" in reason):       #TO BE MORE PRECISE
        sexism = 1
    if ("homophobia" in reason):
        homophobia = 1
    if ("racism" in reason):
        rascism = 1
    if ("backseat" in reason):
        backseat = 1
    if ("spam" in reason):
        spam = 1
    if ("name" in reason):
        username = 1
    if (not sexism and not homophobia and not rascism and not backseat and not spam and not username and commented):
        other = 1

    return ([permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other])



def convert_expire_time(start_date,expire_date):
    if expire_date=="":
        return 0
    else:
        now = str(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        expire = expire_date.replace("T"," ").replace("Z","")

        format = '%Y-%m-%d %H:%M:%S'  # The format Take care it might add 1min
        now_datetime = datetime.strptime(now, format)
        expire_datetime = datetime.strptime(expire, format)
        return (expire_datetime-now_datetime).seconds 

if __name__ == '__main__':
    convert_expire_time("2022-12-23T09:23:05Z")
