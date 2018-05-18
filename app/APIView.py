import datetime

from app import app, db
from app.models import *
from flask import request, jsonify
from sqlalchemy import exc, or_
import json

NOTICE_TAGS = {'캠퍼스': ['자연과학캠퍼스', '인문사회캠퍼스'],
               '전공대학': [ '유학대학', '문과대학', '사회과학대학', '경제대학', '경영대학', '사범대학', '예술대학', '자연과학대학',
                            '정보통신대학', '소프트웨어대학', '공과대학', '약학대학', '생명공학대학', '스포츠과학대학', '의과대학',
                            '성균융합원'],
               '전공학과' : ['유학동양학과', '국어국문학과', '영어영문학과', '프랑스어문학과', '중어중문학과', '독어독문학과', '러시아어문학과', '한문학과', '사학과', '철학과', '문헌정보학과',
                            '글로벌리더학부', '행정학과', '정치외교학과', '신문방송학과', '사회학과', '사회복지학과', '심리학과', '소비자가족학과', '아동청소년학과', '경제학과', '통계학과',
                            '글로벌경제학과', '교육학과', '한문교육과', '수학교육과', '컴퓨터교육과', '미술학과', '디자인학과', '무용학과', '영상학과', '연기예술학과', '의상학과',
                            '생명과학과', '수학과', '물리학과', '화학과', '전자전기공학부', '반도체시스템공학과', '컴퓨터공학과', '소프트웨어학과', '화학공학과', '고분자공학부', '신소재공학부',
                            '기계공학부', '건설환경공학부', '시스템경영공학과', '건축학과', '나노공학과', '약학과', '식품생명공학과', '바이오메카트로닉스학과', '융합생명공학과', '스포츠과학과',
                            '의예과', '의학과', '글로벌바이오메디컬공학과'],
               '재학학기': ['1학기', '2학기', '3학기', '4학기', '5학기', '6학기', '7학기', '8학기', '초과학기'],
               '재학여부': ['재학생', '휴학생'],
               '성별': ['남자', '여자']}


# NOTICE_TAGS = ['자과캠', '인사캠', '유학', '문과', '법과', '사회과학', '경제',
#                 '경영', '사범', '예술', '자연과학', '정보통신', '소프트웨어',
#                 '공과', '약학', '생명공학', '스포츠과학' '의과', '융합',
#                 '1학기', '2학기', '3학기', '4학기', '5학기', '6학기', '7학기', '8학기', '초과학기',
#                 '재학생', '휴학생', '남자', '여자']


def pearson_similarity(vector1, vector2):
    import numpy as np
    if np.linalg.norm(vector1) == 0 or np.linalg.norm(vector2) == 0:
        return 0
    return np.corrcoef(vector1, vector2)[0][1]


def tags2list(tags):
    return str(tags).strip('[').strip(']').split(', ')


def tagspoints2list(user):
    tags_point = json.loads(user.tags)

    tags = sorted(tags_point.keys())
    points = [tags_point[t] for t in tags]
    return tuple(tags), tuple(points)  # (), ()


def object2dict(obj):
    d = {}
    for column in obj.__table__.columns:
        d[column.name] = str(getattr(obj, column.name))
    del d['id']
    return d


def objects2dict(objs):
    ds = []
    for obj in objs:
        ds.append(object2dict(obj))

    return ds


def get_notice_filtered(campus, college, major, semester, is_attending, gender):
    campuses = NOTICE_TAGS['캠퍼스']
    colleges = NOTICE_TAGS['전공대학']
    majors = NOTICE_TAGS['전공학과']
    semesters = NOTICE_TAGS['재학학기']
    is_attendings = NOTICE_TAGS['재학여부']
    genders = NOTICE_TAGS['성별']

    if semester <= 8:
        semester = str(semester) + "학기"
    else:
        semester = "초과학기"

    if is_attending is True:
        is_attending = '재학생'
    else:
        is_attending = '휴학생'

    if gender == 'M':
        gender = '남자'
    else:
        gender = '여자'

    try:
        colleges.remove(college)
    except ValueError:
        pass
    notices = Notice.query.filter(
        or_(Notice.tags.any(Tag.tag.in_([campus])), ~Notice.tags.any(Tag.tag.in_(campuses)))) \
        .filter(~Notice.tags.any(Tag.tag.in_(colleges))) \
        .filter(or_(Notice.tags.any(Tag.tag.in_([major])), ~Notice.tags.any(Tag.tag.in_(majors)))) \
        .filter(or_(Notice.tags.any(Tag.tag.in_([semester])), ~Notice.tags.any(Tag.tag.in_(semesters)))) \
        .filter(or_(Notice.tags.any(Tag.tag.in_([is_attending])), ~Notice.tags.any(Tag.tag.in_(is_attendings)))) \
        .filter(or_(Notice.tags.any(Tag.tag.in_([gender])), ~Notice.tags.any(Tag.tag.in_(genders)))).order_by(Notice.created_datetime).all()
    return list(reversed(notices))


def get_activity_rcmed(user, activities):
    user_tags, user_points = tagspoints2list(user)  # (), ()
    activities_tags = []

    for activity in activities:
        activity_tags = [1 if tag in tags2list(activity.tags) else 0 for tag in user_tags]
        activity_sim = pearson_similarity(list(user_points), list(activity_tags))

        activities_tags.append((activity.uuid, activity_sim))
    activities_tags = sorted(activities_tags, key=lambda x: x[1], reverse=True)
    return activities_tags


def recommend_notice(filter, user, page):
    # user : object
    recommends = []
    num_each_page = 10
    start = (page - 1) * num_each_page
    if filter == 0:
        notices = list(reversed(Notice.query.all()))[start:start + num_each_page]
        for notice in notices:
            obj = {}
            obj['uuid'] = notice.uuid
            recommends.append(obj)
    else:
        campus = user.campus
        major = user.major
        college = user.college
        semseter = user.semester
        is_attending = user.is_attending
        gender = user.gender
        notices = get_notice_filtered(campus, college, major, semseter, is_attending, gender)[start:start + num_each_page]

        for notice in notices:
            obj = {}
            obj['uuid'] = notice.uuid
            tags = notice.tags
            if str(tags) == '[]':
                obj['tags'] = ['전체공통']
            else:
                obj['tags'] = tags2list(tags)
            recommends.append(obj)
    return recommends


def recommend_activity(filter, user, page):
    recommends = []
    num_each_page = 10
    start = (page - 1) * num_each_page
    current_time = datetime.utcnow()
    activities = list(reversed(db.session.query(Activity).filter(Activity.end_date > current_time).all()))

    if filter == 0:
        activities = activities[start:start + num_each_page]
        for activity in activities:
            obj = {}
            obj['uuid'] = activity.uuid
            recommends.append(obj)
    else:
        activities = get_activity_rcmed(user, activities)[start:start + num_each_page]
        for activity in activities:
            obj = {}
            obj['uuid'] = activity[0]
            obj['sim'] = activity[1]
            tags = Activity.query.filter_by(uuid=activity[0]).first().tags
            if str(tags) == '[]':
                obj['tags'] = ['전체공통']
            else:
                obj['tags'] = tags2list(tags)
            recommends.append(obj)

    return recommends


@app.route('/')
def index():
    return "hello world", 200


# return ALL user with dict format
@app.route('/users')
def users():
    users = User.query.all()
    return jsonify(objects2dict(users)), 200


@app.route('/user/<uuid>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def user(uuid):
    method = request.method
    if method == 'GET':
        user = User.query.filter_by(uuid=uuid).first()

        if user is None:
            return "User {} does not exist".format(uuid), 400

        user_tags = {}
        tags, points = tagspoints2list(user)
        for tag, point in zip(tags, points):
            user_tags[tag] = point

        user = object2dict(user)
        user['tags'] = user_tags
        return jsonify(user), 200

    elif method == 'POST':
        print(request)
        print(request.json)
        new_user = request.json
        new_user['uuid'] = uuid

        user = User(new_user)
        db.session.add(user)
        try:
            db.session.commit()
        except exc.IntegrityError:
            print('IntegrityError')
            return "User {} already exist".format(uuid), 400

        return jsonify(new_user), 200

    elif method == 'PATCH':
        user = User.query.filter_by(uuid=uuid)
        if user.first() is None:
            return "User {} does not exist".format(uuid), 200
        user.update(request.json)
        db.session.commit()
        user = request.json
        user['uuid'] = uuid

        return jsonify(user), 200

    elif method == 'DELETE':
        user = User.query.filter_by(uuid=uuid).first()
        if user is None:
            return "User {} does not exist".format(uuid), 400
        db.session.delete(user)
        db.session.commit()
        return "User {} is deleted".format(uuid), 400
    else:
        return "Invalid request method", 400


@app.route('/notice', methods=['GET', 'POST', 'DELETE'])
def notice():
    method = request.method
    if method == 'GET':
        user_uuid = request.args.get('user_uuid')
        page = request.args.get('page')
        filter = request.args.get('filter')
        if not user_uuid or not page or not filter:
            return "Invalid request parameter", 400
        try:
            page = int(page)
            filter = int(filter)
        except ValueError:
            return "Invalid request parameter", 400
        user = User.query.filter_by(uuid=user_uuid).first()
        if user is None:
            return "User {} does not exist".format(user_uuid), 400
        return jsonify(recommend_notice(filter, user, page))

    elif method == 'POST':
        notices = request.json
        if notices is None:
            return "Invalid request body", 400
        add_uuids = []
        for notice in notices:
            try:
                n = Notice(notice)
                db.session.add(n)
                db.session.commit()
                add_uuids.append(n.uuid)
                # print(n.tags)
            except exc.IntegrityError:
                db.session.rollback()
        return jsonify(add_uuids), 200

    elif method == 'DELETE':
        # uuids = request.json['uuids']
        # for uuid in uuids:
        #     notice = Notice.query.filter_by(uuid=uuid).first()
        #     if notice is None:
        #         return "Notice {} does not exist".format(uuid)
        #     db.session.delete(notice)
        # db.session.commit()
        # return jsonify(uuids), 200
        uuids = []
        notices = Notice.query.all()
        uuids.append(len(notices))
        for notice in notices:
            uuids.append(notice.uuid)
            db.session.delete(notice)
        db.session.commit()

        return jsonify(uuids), 200

    else:
        return "Invalid request method", 400


@app.route('/activity', methods=['GET', 'POST', 'DELETE'])
def activity():
    method = request.method
    if method == 'GET':
        user_uuid = request.args.get('user_uuid')
        page = request.args.get('page')
        filter = request.args.get('filter')
        if not user_uuid or not page or not filter:
            return "Invalid request parameter", 400
        try:
            page = int(page)
            filter = int(filter)
        except ValueError:
            return "Invalid request parameter", 400
        user = User.query.filter_by(uuid=user_uuid).first()
        if user is None:
            return "User {} does not exist".format(user_uuid), 400
        return jsonify(recommend_activity(filter, user, page)), 200

    elif method == 'POST':
        activities = request.json
        if activities is None:
            return "Invalid request body", 400
        add_uuids = []
        for activitiy in activities:
            try:
                n = Activity(activitiy)
                db.session.add(n)
                db.session.commit()
                add_uuids.append(n.uuid)
                # print(n.tags)
            except exc.IntegrityError:
                db.session.rollback()
        return jsonify(add_uuids), 200

    elif method == 'DELETE':
        uuids = []
        activities = Activity.query.all()
        uuids.append(len(activities))
        for activity in activities:
            uuids.append(activity.uuid)
            db.session.delete(activity)
        db.session.commit()

        return jsonify(uuids), 200

    else:
        return "Invalid request method", 400


@app.route('/tag', methods=['POST', 'GET', 'DELETE'])
def tag():
    method = request.method
    if method == 'POST':
        tags = request.json
        for tag in tags:
            t = Tag(tag)
            db.session.add(t)
            try:
                db.session.commit()
            except exc.IntegrityError:
                db.session.rollback()
        return jsonify(tags), 200
    elif method == 'GET':
        tags = []
        for tag in Tag.query.all():
            tags.append(tag.tag)
        return jsonify(sorted(tags)), 200
    elif method == 'DELETE':
        tags = request.json
        for tag in tags:
            t = Tag.query.filter_by(tag=tag).first()
            if t is not None:
                db.session.delete(t)
                db.session.commit()
        print(Tag.query.all())
        return jsonify(tags), 200
    else:
        return "Invalid request method", 400


@app.route('/notice/<uuid>', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def notice_test(uuid):
    method = request.method
    if method == 'DELETE':
        notice = Notice.query.filter_by(uuid=uuid).first()
        if notice is None:
            return "Notice {} does not exist".format(uuid), 400
        db.session.delete(notice)
        db.session.commit()
        return "Notice {} is deleted".format(uuid), 200


    # ***get all notice uuid (to test)
    elif method == 'GET':
        notices = Notice.query.all()
        return jsonify(objects2dict(notices))
        # uuids = []
        # print(notices)
        # for notice in notices:
        #     uuids.append(notice.uuid)
        # return jsonify(uuids), 200
