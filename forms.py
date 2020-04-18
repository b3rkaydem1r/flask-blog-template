from wtforms import Form, StringField, TextAreaField, PasswordField, validators


class RegisterForm(Form):
    name = StringField('Name', validators=[validators.Length(min = 4, max = 25)])
    username = StringField('Username', validators=[validators.Length(min = 5, max = 20)])
    email = StringField('Email', validators=[validators.Length(min = 6, max = 35), validators.Email()])
    password = PasswordField('Password', validators=[
        validators.DataRequired(),
        validators.EqualTo(fieldname = 'confirm')
    ])
    confirm = PasswordField('Confirm Password')


class LoginForm(Form):
    username = StringField('Username')
    password = PasswordField('Password')


class PostForm(Form):
    title = StringField('Post Title', validators = [validators.Length(max = 150)])
    content = TextAreaField('Post Content')


class CommentForm(Form):
    comment = TextAreaField('Comment', validators= [validators.Length(max = 600)])