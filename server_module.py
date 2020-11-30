import json
from flask import render_template, request, redirect
from werkzeug.utils import secure_filename

import sqlite3 as sql

ESSAYNUM = 3
DATABASENAME = 'database.db'


class Authentication:
    def __init__(self, login, password):
        self.login = login
        self.password = password


class User(Authentication):
    def __init__(self, login='', password='', institution='MIPT'):
        super().__init__(login, password)
        self.institution = institution

    def upload(self, file_name):
        user_info_dict = {"login": self.login, "password": self.password, "institution": self.institution}

        with open(file_name, "w") as write_file:
            json.dump(user_info_dict, write_file)


def make_database(base_name):
    con = sql.connect(base_name)

    with con:
        cursor = con.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS `users` (loginTEXT, passwordTEXT, institutionTEXT, userID)")
        cursor.execute("CREATE TABLE IF NOT EXISTS `essays_authors` (authorID, essayID)")
        cursor.execute("CREATE TABLE IF NOT EXISTS `essays` (titleTEXT, essay BLOB, essayID, type)")
        cursor.execute("CREATE TABLE IF NOT EXISTS `essays_tags` (tagsTEXT, essayID)")
        cursor.execute("CREATE TABLE IF NOT EXISTS `essays_used` (userID, institutionTEXT, essayID)")

        con.commit()


def login_db(login, password):
    with sql.connect(DATABASENAME) as con:
        cursor = con.cursor()

    cursor.execute(f"SELECT count(distinct userID) From users Where loginTEXT = '{login}'")

    number_login = int(cursor.fetchall()[0][0])

    if number_login == 1:
        cursor.execute(f"SELECT count(distinct passwordTEXT) From users Where loginTEXT = '{login}"
                       f"' and passwordTEXT = '{password}'")

        login_password_num = cursor.fetchall()[0][0]
        if login_password_num == 1:
            cursor.execute(
                f"SELECT distinct institutionTEXT From users Where loginTEXT = '{login}"
                f"' and passwordTEXT = '{password}'")
            institution = cursor.fetchall()[0][0]
            new_user = User(login, password, institution)
            return new_user
        else:
            return 0
    else:
        return 0


def find_user_from_login(login):
    with sql.connect(DATABASENAME) as con:
        cursor = con.cursor()

    cursor.execute(f"SELECT count(distinct userID) From users Where loginTEXT = '{login}'")
    number_login = cursor.fetchall()[0][0]

    if number_login == 1:
        cursor.execute(f"SELECT distinct passwordTEXT, institutionTEXT From users Where loginTEXT = '{login}'")
        this_user_data = cursor.fetchall()
        password = this_user_data[0][0]
        institution = this_user_data[0][1]

        return User(login, password, institution)
    else:
        return 0


def find_use_id_from_login(login):
    with sql.connect(DATABASENAME) as con:
        cursor = con.cursor()

    cursor.execute(f"SELECT distinct userID From users Where loginTEXT = '{login}'")

    return cursor.fetchall()[0][0]


def get_essay_for_user(this_user, tagsArray):
    with sql.connect(DATABASENAME) as con:
        cursor = con.cursor()

    user_id = find_use_id_from_login(this_user.login)

    sql_text = ""

    for i in range(0, len(tagsArray) - 1):
        sql_text += f"Select distinct essayID from essays_tags Where tagsTEXT = '{tagsArray[i]}'"
        sql_text += " INTERSECT "

    sql_text += f"Select distinct essayID from essays_tags Where tagsTEXT = '{tagsArray[-1]}'"

    sql_text += f"except select distinct essayID from essays_used, (select distinct " \
                f"institutionTEXT from users where " f"userID = {user_id}) as usedInst where " \
                f"essays_used.institutionTEXT = usedInst.institutionTEXT "

    cursor.execute(sql_text)
    essay_id_array = cursor.fetchall()
    if not essay_id_array:
        return False
    else:
        number = min(ESSAYNUM, len(essay_id_array))
        array_id = [x for [x, ] in essay_id_array[:number]]
        answer = []
        for id_ in array_id:
            cursor.execute(f"select distinct essay, titleTEXT, type from essays where essayID = {id_}")
            ThisEssayData = cursor.fetchall()
            answer.append((ThisEssayData[0][0], ThisEssayData[0][1], ThisEssayData[0][2]))

        return answer


def add_user_db(newUser):
    with sql.connect(DATABASENAME) as con:
        cursor = con.cursor()

    cursor.execute(f"select count(loginTEXT) from users where loginTEXT = '{newUser.login}'")
    same_login_num = cursor.fetchall()[0][0]

    if same_login_num == 0:
        cursor.execute(f"select count(userID) from users ")
        users_num = cursor.fetchall()[0][0]
        if users_num == 0:
            new_user_id = 1
        else:
            cursor.execute("select min(userID) from (select distinct userID from users except "
                           "select distinct A.userID from users as A, users as B where "
                           "A.userID + 1 = B.userID) as T")
            new_user_id = cursor.fetchall()[0][0] + 1
        cursor.execute(f"INSERT INTO users VALUES ('{newUser.login}', '{newUser.password}', "
                       f"'{newUser.institution}', "
                       f"{new_user_id})")

        con.commit()
        return True
    else:
        return False


def add_essay_db(essay, title, tags_array, this_user, Type):
    with sql.connect(DATABASENAME) as con:
        cursor = con.cursor()
    cursor.execute(f"select count(essayID) from essays ")

    if cursor.fetchall()[0][0] == 0:
        new_essay_id = 1
    else:
        cursor.execute("select min(essayID) from (select distinct essayID from essays except select "
                       "distinct A.essayID from (select essayID from essays) as A, (select essayID "
                       "from essays) as B where A.essayID + 1 = B.essayID) as T")
        new_essay_id = cursor.fetchall()[0][0] + 1

    this_user_id = find_use_id_from_login(this_user.login)
    binary = sql.Binary(essay)
    cursor.execute(f"insert into essays values ('{title}', ?, {new_essay_id}, '{Type}')", (binary,))
    cursor.execute(f"insert into essays_authors values ({this_user_id}, {new_essay_id})")
    cursor.execute(f"insert into essays_used values ({this_user_id}, '{this_user.institution}', {new_essay_id})")

    for tag in tags_array:
        cursor.execute(f"insert into essays_tags values ('{tag}', {new_essay_id})")

    con.commit()


class UserManager:
    @staticmethod
    def add(new_user):
        response = add_user_db(new_user)

        if not response:
            return None

    @staticmethod
    def login(user):
        response = login_db(user.login, user.password)
        if isinstance(response, User):
            return response

        return None

    @staticmethod
    def get(username):
        return find_user_from_login(username)


class Essay:
    def __init__(self, title, file_name, author, tags=None):
        if tags is None:
            tags = []

        self.title = title
        self.file_name = file_name
        self.tags = tags
        self.author = author

    def __contains__(self, item):
        return item in self.tags

    def to_dict(self):
        dictionary = {'title': self.title, 'file_name': self.file_name,
                      'tags': self.tags, 'author': self.author}

        return dictionary


class EssayManager:
    @staticmethod
    def add(loading_file, essay, file_type):
        if not isinstance(essay, Essay):
            raise TypeError('DataBase.add need Essay, got ', type(essay), ' instead\n')

        add_essay_db(loading_file.read(), essay.title, essay.tags, find_user_from_login(essay.author), file_type)

    @staticmethod
    def find(username, tags):
        return get_essay_for_user(find_user_from_login(username), tags)


def user(diction):
    return render_template('user.html', user=diction)


def check_to_be_new(essays):
    for i in range(len(essays)):
        index = 1
        for j in range(i + 1, len(essays)):
            if essays[i][1] == essays[j][1]:
                essays[j] = (essays[j][0], essays[j][1] + str(index), essays[j][2])
                index += 1

    for i in range(len(essays)):
        essays[i] = (essays[i][0], essays[i][1] + essays[i][2], essays[i][2])


class Server:
    def __init__(self):
        self.manager = UserManager()
        self.base = EssayManager()
        self.searched = []
        self.error_message = ''

    def create_account(self):
        new_user = User(request.form['uname'], request.form['psw'], request.form['institution'])

        if not add_user_db(new_user):
            self.error_message = 'Sorry, this login is already taken.\n'
            return redirect('/new_account')
        return redirect('/')

    def main_creating_account_page(self):
        if self.error_message != '':
            error_message = self.error_message
            self.error_message = ''
            return render_template('creating_account.html', error=error_message)

        return render_template('creating_account.html')

    def login(self):
        name = request.form['uname']
        psw = request.form['psw']

        auth = Authentication(name, psw)

        real_user = self.manager.login(auth)

        if real_user is not None:
            return redirect('/user/' + name)
        else:
            return redirect('/')

    def user_main(self, username):
        diction = {'name': username}

        if self.searched:
            diction['loaded_files'] = self.searched
            self.searched = []

        return render_template('user.html', user=diction)

    def upload_essay(self, username):
        title = str(request.form['title'])
        tags = request.form['tags'].split('/')

        loading_file = request.files['file']

        file_type = str(secure_filename(loading_file.filename)).rsplit('.')[1]

        essay = Essay(title, '', username, tags)
        self.base.add(loading_file, essay, '.' + file_type)

        if username == 'new_maker_test':
            return redirect('/')

        return redirect(request.referrer)

    def search(self, username):
        tags = str(request.form['tag'])

        essays = self.base.find(username, list(tags.split('/')))

        if not essays:
            return redirect('/user/' + username)

        check_to_be_new(essays)

        self.searched = [essay[1] for essay in essays]  # [essay.file_name for essay in proper_essays]

        for essay in essays:
            with open("static/" + essay[1], 'wb') as file_out:
                file_out.write(essay[0])

        return redirect('/user/' + username)

    def alright(self, essay, ask_user):
        author = self.manager.get(essay.author)

        return author.institution != ask_user.institution
