import nltk
nltk.download('punkt')

from pymorphy2 import MorphAnalyzer
from random import uniform, randint
import pandas as pd
import pickle
import re

morph = MorphAnalyzer()

def detect_case(ngram):
  v = ''
  p = ''
  n = ''
  if 'INFN' in morph.parse(ngram[0])[0].tag:
    v = ngram[0]
  if 'INFN' in morph.parse(ngram[0])[0].tag and 'NOUN' in morph.parse(ngram[1])[0].tag:
    # detect gender
    if 'femn' in morph.parse(ngram[1])[0].tag:
      n = morph.parse(ngram[1])[0].inflect({'accs'}).word
    else:
#             n = morph.parse(ngram[1])[0].inflect({'nomn'}).word
      n = morph.parse(ngram[1])[0].inflect({'accs'}).word
  if 'PREP' in morph.parse(ngram[1])[0].tag and 'NOUN' in morph.parse(ngram[2])[0].tag:
#         detect need case
    p = ngram[1]
    if ngram[1] in ('под','над','с','за','между'):
      n = morph.parse(ngram[2])[0].inflect({'ablt'}).word
    elif ngram[1] in ('о','об','во','в','на','при'):
      n = morph.parse(ngram[2])[0].inflect({'loct'}).word
    else:
      n = morph.parse(ngram[2])[0].inflect({'datv'}).word
  return (v,p,n)

def join_s(l=[]):
  result = ' '.join(l)
  return re.sub('\s{2,}', ' ', result)

def case_place(ngram=[]):
  p = ''
  n = ''
  if 'PREP' in morph.parse(ngram[0])[0].tag:
	  p = ngram[0]
	  n = ngram[1]
	  if p in ('к','по'):
	    # dativ
	    n = morph.parse(n)[0].inflect({'datv'}).word
	  elif p in ('у','вокруг'):
	    # roditel
	    n = morph.parse(n)[0].inflect({'gent'}).word
	  elif p in ('через'):
	    # accs
	    n = morph.parse(n)[0].inflect({'accs'}).word
	  elif p in ('под','над','между','за'):
	    # tvorit
	    n = morph.parse(n)[0].inflect({'ablt'}).word
	  elif p in ('в','на'):
	    # predlochn
	    n = morph.parse(n)[0].inflect({'loct'}).word
  else:
    n = morph.parse(ngram)[0].inflect({'gent'}).word
  return (p,n)


def search_back(word,_dict={}):
  tmp_seq = _dict.get(word)
  f_word = unirand(tmp_seq)
  if 'PREP' in morph.parse(f_word)[0].tag:
    s_word = unirand(_dict.get(f_word))
    return join_s(detect_case([s_word,f_word,word]))
  else:
    return join_s(detect_case([f_word,word]))
      
def search_back_2dict(word,_dict_noun={},_dict_verb={}):
  tmp_seq = _dict_noun.get(word)
  f_word = unirand(tmp_seq)
  if 'PREP' in morph.parse(f_word)[0].tag:
    s_word = unirand(_dict_verb.get(f_word))
    return join_s(detect_case([s_word,f_word,word]))
  else:
    return join_s(detect_case([f_word,word]))

def search_front(word,_dict):
  tmp_seq = _dict.get(word)
  try:
    f_word = unirand(tmp_seq)
    if 'PREP' in morph.parse(f_word)[0].tag:
      s_word = unirand(_dict.get(f_word))
      return join_s(case_place((f_word,s_word)))
    else:
      return join_s(case_place((f_word)))
  except TypeError:
    return ''

# simple randomise for model {word} -> {words list}
def unirand(seq):
  sum_, freq_ = 0, 0
  for item, freq in seq:
    sum_ += freq
#         print(sum_)
  rnd = uniform(0, sum_)
#     print(rnd)
  for token, freq in seq:
    freq_ += freq
    if rnd < freq_:
      return token


with open('NOUN_VERBorPREP(new).pickle', 'rb') as f:
  data_noun = pickle.load(f)
with open('PREP_VERB(new).pickle', 'rb') as f:
  data_verb = pickle.load(f)


df_place = pd.read_csv('verb_prep_noun(place).csv')
del df_place['Unnamed: 0']
df_place.fillna(value='',inplace=True)

df_pers = pd.read_csv('verb_prep_noun(persons).csv')
del df_pers['Unnamed: 0']
df_pers.fillna(value='', inplace=True)


def choise_place(verb, df):
  try:
    tmp_df = df[df['VERB']==verb]
    n = tmp_df.shape[0]
    rand_n = randint(0,n-1)
    tpl = tmp_df.iloc[rand_n]
    return (tpl[1],tpl[2])
  except:
    return False

# choise phrase by verb
def make_phrase(target, func_make):
  if target:
    return join_s(func_make(target))
  else:
    return ''

### choise case for agrive
def detect_case_place(ngram):
  if ngram[0] in ('по','к'):
    return (ngram[0],morph.parse(ngram[1])[0].inflect({'datv'}).word) # datel
  elif ngram[0] in ('в','на','при','об','о'):
    return (ngram[0],morph.parse(ngram[1])[0].inflect({'loct'}).word) # predloch
  elif ngram[0] in ('после','из','до','от','около'):
    return (ngram[0],morph.parse(ngram[1])[0].inflect({'gent'}).word) # roditel
  elif ngram[0] in ('над','под','c'):
    return (ngram[0],morph.parse(ngram[1])[0].inflect({'ablt'}).word) # tvorit
  else:
    return (ngram[0],morph.parse(ngram[1])[0].inflect({'accs'}).word) # vinit


def rand_phrase():
  w = list(data_noun.keys())[randint(0,15788)]
  main_tuple = search_back_2dict(w,data_noun,data_verb).split(' ')
  place_tuple = choise_place(main_tuple[0],df_place)
  pers_tuple = choise_place(main_tuple[0], df_pers)
  _s = ''
  if main_tuple:
    _s += make_phrase(main_tuple,detect_case) + ' '
  if place_tuple:
    _s += make_phrase(place_tuple, detect_case_place) + ' '
#       print('in if')
  if pers_tuple:
    _s += make_phrase(pers_tuple, detect_case_place)
#   print(_s.strip())
  return (_s.strip())
# print(main, place, pers)


def random_phrase():
  phrase = ('Сделаем попытку:', 'Попробуем:', 'Заставь меня:')[randint(0,2)]
  return phrase


def random_resource():
  return join_s((random_phrase(), rand_phrase()))


import telebot
from telebot import types

token = '825798287:AAFUPscDI_zOR92EOCO0v2bFfukKoZe6mUE'
# Anrkhn_token = '662652606:AAF8wg4KCf3RHnbkc_hNpIK5ShHDJWjexrQ'
_bot = telebot.TeleBot(token)

markup_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
btn_example = types.KeyboardButton('пример')
btn_example1 = types.KeyboardButton('работаешь?')
markup_menu.add(btn_example,btn_example1)

# отклик на команду /start
@_bot.message_handler(commands=['start'])
def send_welcome(message):
  _bot.send_message(message.chat.id, "Да, я работаю!!!", reply_markup=markup_menu)

# отклик на команду /empl
@_bot.message_handler(commands=['empl'])
def send_example(message):
  _bot.send_message(message.chat.id, random_resource(), reply_markup=markup_menu)

# обработка контекстных кнопок
@_bot.message_handler(func=lambda message: True)
def send_example(message):
	try:
	  if message.text == 'пример':
	    _bot.send_message(message.chat.id, random_resource(), reply_markup=markup_menu)
	  elif message.text == 'работаешь?':
	    _bot.send_message(message.chat.id, 'Тружусь, тружусь...', reply_markup=markup_menu)
	except:
		_bot.send_message(message.chat.id, 'Упс... попытайся ещё раз...', reply_markup=markup_menu)

_bot.polling()
