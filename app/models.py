from app import db
from datetime import datetime
from sqlalchemy import update, and_, select
from sqlalchemy import create_engine


# user_tags = db.Table('user_tags',
#                      db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
#                                primary_key=True),
#                      db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'),
#                                primary_key=True),
#                      db.Column('point', db.Float, default=0))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(80), default=None, unique=True)
    university = db.Column(db.String(80), default=None)
    campus = db.Column(db.String(80), default=None)
    college = db.Column(db.String(80), default=None)
    major = db.Column(db.String(80), default=None)
    double_major = db.Column(db.String(80), default=None)
    semester = db.Column(db.Integer, default=None)
    is_attending = db.Column(db.Boolean, default=None)
    gender = db.Column(db.String(1))
    # tags = db.relationship('Tag', secondary=user_tags,
    #                        lazy='subquery', backref=db.backref('users', lazy=True))
    tags = db.Column(db.Text)

    def __init__(self, kwargs):
        tags = kwargs.get('tags')

        self.uuid = kwargs.get('uuid')
        self.university = kwargs.get('university')
        self.campus = kwargs.get('campus')
        self.college = kwargs.get('college')
        self.major = kwargs.get('major')
        self.semester = kwargs.get('semester')
        self.is_attending = kwargs.get('is_attending')
        self.gender = kwargs.get('gender')

        tags = self.set_tags(tags)

        self.set_tags_points(tags)

    def set_tags(self, tags):
        if self.campus == '자연과학캠퍼스':
            tags.append('자과캠')
        else:
            tags.append('인사캠')

        tags.append(self.college)
        tags.append(self.major)

        if self.semester <= 8:
            tags.append(str(self.semester) + '학기')
        else:
            tags.append('초과학기')

        if self.is_attending is True:
            tags.append('재학생')
        else:
            tags.append('휴학생')

        if self.gender == 'M':
            tags.append('남자')
        else:
            tags.append('여자')
        return tags

    def set_tags_points(self, tags):
        all_tags = Tag.query.all()
        dict = {}
        for tag in all_tags:
            if tag.tag in tags:
                dict[tag.tag] = 1
            else:
                dict[tag.tag] = 0
        self.tags = str(dict).replace("'", '"')

    def __repr__(self):
        return '<User {}>'.format(self.uuid)


notice_tags = db.Table('notice_tags',
                       db.Column('notice_id', db.Integer, db.ForeignKey('notice.id'),
                                 primary_key=True),
                       db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'),
                                 primary_key=True))


class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(80), unique=True)
    university = db.Column(db.String(80))
    title = db.Column(db.String(80))
    url = db.Column(db.String(80))
    created_datetime = db.Column(db.DateTime, nullable=True)
    content = db.Column(db.Text)
    tags = db.relationship('Tag', secondary=notice_tags,
                           lazy='subquery', backref=db.backref('notices', lazy=True))

    def __init__(self, kwargs):
        self.uuid = kwargs.get('uuid')
        self.university = kwargs.get('university')
        self.title = kwargs.get('title')
        self.url = kwargs.get('url')
        self.content = kwargs.get('content')
        if kwargs.get('created_datetime') is None:
            self.created_datetime = None
        else:
            self.created_datetime = datetime.strptime(kwargs.get('created_datetime'), "%Y-%m-%d")

        tags = kwargs.get('tags')

        self.set_tags(tags)

    def set_tags(self, tags):
        if not len(tags):
            return
        for tag in tags:
            t = Tag.query.filter_by(tag=tag).first()
            if t is not None:
                self.tags.append(t)

        return

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.uuid + " : " + str(self.tags)


activity_tags = db.Table('activity_tags',
                         db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'),
                                   primary_key=True),
                         db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'),
                                   primary_key=True))


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(80), unique=True)
    title = db.Column(db.String(80))
    host = db.Column(db.String(80))
    end_date = db.Column(db.DateTime, nullable=True)
    url = db.Column(db.String(80))
    content = db.Column(db.Text)  # parsed content
    tags = db.relationship('Tag', secondary=activity_tags,
                           lazy='subquery', backref=db.backref('activities', lazy=True))

    def __init__(self, kwargs):
        self.uuid = kwargs.get('uuid')
        self.title = kwargs.get('title')
        self.host = kwargs.get('host')
        if kwargs.get('end_date') is None:
            self.end_date = None
        else:
            self.end_date = datetime.strptime(kwargs.get('end_date'), "%Y-%m-%d")
        self.url = kwargs.get('url')
        self.content = kwargs.get('content')
        tags = kwargs.get('tags')

        self.set_tags(tags)

    def set_tags(self, tags):
        if not len(tags):
            return
        for tag in tags:
            t = Tag.query.filter_by(tag=tag).first()
            if t is not None:
                self.tags.append(t)

        return

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.uuid + " : " + str(self.tags)


# [Notice]
# 캠퍼스 : 자과캠, 인사캠
# 대학 : 유학, 문과, 법과, 사회과학, 경제, 경영, 사범, 예술, 자연과학,
#       정보통신, 소프트웨어, 공과, 약학, 생명공학, 스포츠과학, 의과, 융합
# 학년: 1학기, 2학기, 3학기, 4학기, 5학기, 6학기, 7학기, 8학기, 초과학기
# 재학: 재학생, 휴학생
# 성별 : 남자, 여자
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(80), unique=True)

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return self.tag

    def __repr__(self):
        return self.tag
