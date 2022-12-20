import datetime

log_folder_path = "logs/"

def init_file_name():
    return ("log_" + str(datetime.date.today()) + ".txt")
log_file_name = init_file_name()
def get_file_name():
    return log_file_name
def start_log():
    f = open(log_folder_path + get_file_name(), 'a')
    f.write("\n          ********** START OF LOG FILE **********          ")
    f.write("\n||| " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " |||\n")
    f.close()
def log(message):
    f = open(log_folder_path + get_file_name(), 'a')
    f.write("[" + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "]: " + message)
    f.write("\n")
    f.close()
def end_log():
    f = open(log_folder_path + get_file_name(), 'a')
    f.write("||| " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " |||\n")
    f.write("          ********** END OF LOG FILE **********          \n")
    f.close()