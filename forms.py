from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, IntegerField, BooleanField,
                     RadioField, ValidationError)
from wtforms.validators import InputRequired, Length


class CreateItemForm(FlaskForm):
    def description_length_check(form, field):
        if len(field.data) > 279:
            raise ValidationError('Name must be less than 280 characters. Please re-enter item with a shorter description.')

    title = StringField('Title', validators=[InputRequired(),
                                             Length(min=1, max=100)])

    gameTypeDropdown = SelectField(u'Game Type',
                                   choices=['---', 'Board Game', 'Card Game', 'Video Game', 'Jigsaw Puzzle',
                                            'Computer Game'],
                                   validators=[InputRequired()])

    description = TextAreaField('Description',
                                validators=[Length(max=280), description_length_check])

    condition = SelectField(u'Condition',
                            choices=['---', 'Mint', 'Like New', 'Lightly Used', 'Moderately Used',
                                     'Heavily Used', 'Damaged/Missing Parts'],
                            validators=[InputRequired()])

    # populated form DB
    platform = SelectField(u'Platform')
    # platform = SelectField(u'Platform',
    #                         choices=['Nintendo', 'PlayStation', 'Xbox'])

    media1 = SelectField(u'Media',
                        choices=['optical disc', 'game card', 'cartridge'])

    media = SelectField(u'Media',
                        choices=['Linux', 'macOS', 'Windows'])

    pieceCount = IntegerField(u'Piece Count')
