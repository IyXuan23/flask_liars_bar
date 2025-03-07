import pytest
from flaskr.db import get_db

def test_index(client, auth):

    #check when not logged in, has options to login/register
    response = client.get('/')
    assert b"Log In" in response.data 
    assert b"Register" in response.data

    #after login, should have option to log out and see available posts
    auth.login()
    response = client.get('/')
    assert b'Log Out' in response.data
    assert b'test title' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/1/update"' in response.data


#check that page asks u to login if you want to create/update/delete
#if you are not logged in
@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))

def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == '/auth/login'

def test_author_required(app, client, auth):
    #purposely change post author to another author, remove power to edit
    #id = 1, is autoincrementing primary key of the database (since we only have 1 entry)
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    #ensure they do not have access to delete/edit if not their own post
    auth.login()
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    #and they dont see the edit link
    assert b'href="/1/delete"' not in client.get('/').data

@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))
#test what happens if user tries to edit/delete non-existent post
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404

#ensure logged in user can successfully make a post
def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={'title': 'created', 'body': ''})

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM post").fetchone()[0]
        assert count == 2

#ensure post can be sucessfully updated by logged in client
def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/update').status_code == 200
    client.post('/1/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'

#test that title must not be empty when creating or editing
@pytest.mark.parametrize('path', (
    '/create',
    '/1/update'
))

def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required' in response.data

#ensure post is successfully deleted by logged in client
def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers["Location"] == '/'

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM post WHERE id = 1").fetchone()
        assert post is None
