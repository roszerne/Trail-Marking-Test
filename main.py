import atexit
import codecs
import csv
import random
from os.path import join
from statistics import mean
from collections import OrderedDict

import yaml
from psychopy import visual, event, logging, gui, core, colors

from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product

''' 
mapowanie punktow z pliku konfiguracyjnego na ekran uzytkownika
    :param Table: tablica z kolkami
    :param Text: tablica z bodzcami tekstowymi
    :param filename: sciezka do pliku z punktami
    :param conf: sciezka do pliku konfiguracyjnego
    :return: message
'''
def ready_coord(Table, Text, filename, conf):
    global SQUARE_SIZE
    global SCREEN_RES
    # przesuniecie punktow
    offset_x = SQUARE_SIZE / 2
    offset_y = SQUARE_SIZE / 2
    # ladowanie pliku
    points = yaml.safe_load(open(filename, encoding='utf-8'))
    map_size = points['MAP_SIZE'] - 1
    n = points['POINTS']
    # przydzielanie wspolrzednych do punktow
    for i in range(1, n + 1):
        new_pos = []
        new_pos = points["POINT_" + str(i)]
        # jezeli punkt wychodzi poza obszar mamy - podnosimy wyjatek i konczymy program
        if new_pos[0] > map_size or new_pos[1] > map_size:
            abort_with_error("Wrong coordinates in the: " + str(filename) + " : " + str(new_pos))
        # zapisanie nowych pozycji dla punktow
        new_pos[0] = (int)((new_pos[0] / map_size) * SQUARE_SIZE) - offset_x - conf["QUE_RADIUS"]/8
        new_pos[1] = (int)((new_pos[1] / map_size) * SQUARE_SIZE) - offset_y - conf["QUE_RADIUS"]/8
        Table[i - 1].pos = new_pos
        Text[i - 1].pos = new_pos
            
    
# Rysowanie kwadratu z ramka na srodku ekranu
def draw_SQUARE(win):
    global SQUARE_SIZE
    global SCREEN_RES
    conf=yaml.safe_load(open('config.yaml', encoding='utf-8'))
    # Drawning frame
    visual.Rect(win = win, size = [SQUARE_SIZE * 1.2, SQUARE_SIZE * 1.2], fillColor = conf['FRAME_COLOR'], colorSpace = 'rgb255').draw()
    # Drawning Square
    visual.Rect(win = win, size = [SQUARE_SIZE* 1.1, SQUARE_SIZE * 1.1], fillColor = conf['FRAME_BACKGROUND'], colorSpace = 'rgb255' ).draw()

@atexit.register
def save_beh_results():
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will broke.
    """
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()

def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    """
    Check (during procedure) if experimentator doesn't want to terminate.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error(
            'Experiment finished by user! {} pressed.'.format(key))


def show_info(win, file_name, mouse, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='white', text=msg,
                          height=30, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    timer = core.CountdownTimer(10) # czekamy 10 sekund na input od uzytkownika
    while timer.getTime() > 0:
        key = event.getKeys(keyList=['f7','esc'])
        if key == ['f7'] or key == ['esc']:
            abort_with_error(
                'Experiment finished by user on info screen! F7 pressed.')
        buttons, times = mouse.getPressed(getTime=True)
        if buttons[0] and times[0] > 0.1:
            win.flip()
            mouse.clickReset(buttons = [0])
            return
    mouse.clickReset(buttons = [0])
    win.flip()

def abort_with_error(err):
    """
    Call if an error occured.
    """
    logging.critical(err)
    raise Exception(err)


# GLOBALS

RESULTS = list()  # list in which data will be colected
RESULTS.append(['PART_ID', 'Trial part', 'Complete Time'])  # ... Results header

def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global
    global SQUARE_SIZE
    global SCREEN_RES
    SCREEN_RES = OrderedDict()
    SCREEN_RES['width'] = 1650
    SCREEN_RES['height'] = 1040

    #SCREEN_RES = get_screen_res() # pobierz rozdzielczosc ekranu 
    print(SCREEN_RES)
    SQUARE_SIZE = SQUARE_SIZE * SCREEN_RES.get("height") # oblicz rozmiar kwadratu
    # === Dialog popup ===
    info={'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg=gui.DlgFromDict(
        dictionary=info, title='Trail Marking Test')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock=core.Clock()
    # load config, all params are there
    conf=yaml.safe_load(open('config.yaml', encoding='utf-8'))
    # === Scene init ===
    win=visual.Window(list(SCREEN_RES.values()), fullscr=False, monitor='testMonitor', units='pix', screen=0, color = conf['BACKGROUND_COLOR'],colorSpace = 'rgb255')
    mouse = event.Mouse(visible=True, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE=get_frame_rate(win)
    # check if a detected frame rate is consistent with a frame rate for witch experiment was designed
    # important only if milisecond precision design is used
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg=gui.Dlg(title="Critical error")
        dlg.addText(
            'Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID=info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'),
                    level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # === Prepare stimulus here ===
    # A Training
    A_test_circles = [ visual.Circle(win,
    name = str(i), 
    radius=conf['QUE_RADIUS'],
    opacity = 1, 
    fillColor=conf['STIM_COLOR'], 
    lineColor=conf['STIM_COLOR'],
    colorSpace = 'rgb255')
    for i in range(1, 9)]

    A_test_texts = [visual.TextStim(win, text = str(i), name = str(i),
    height = conf['QUE_RADIUS'], 
    color = conf['STIM_LETTER_COLOR'],
    colorSpace = 'rgb255') 
    for i in range(1, 9)]

    ready_coord(A_test_circles, A_test_texts, "trail\\A_test.yaml", conf)
    # A trail
    A_circles = [ visual.Circle(win,
    name = str(i), 
    radius=conf['QUE_RADIUS'], 
    fillColor=conf['STIM_COLOR'], 
    lineColor=conf['STIM_COLOR'],
    colorSpace = 'rgb255')
    for i in range(1, 26)]

    A_texts = [visual.TextStim(win, text = str(i), name = str(i),
    height = conf['QUE_RADIUS'], 
    color = conf['STIM_LETTER_COLOR'],
    colorSpace = 'rgb255') 
    for i in range(1, 27)]

    ready_coord(A_circles, A_texts, "trail\\A_trail.yaml", conf)
    # B Training
    B_test_texts = []
    for i in range(1, 9):
            text = chr(i//2 + 64) if i % 2 == 0 else str(i//2 + 1)
            B_test_texts.append(visual.TextStim(win, text = str(text),
            height = conf['QUE_RADIUS'], 
            color = conf['STIM_LETTER_COLOR'],colorSpace = 'rgb255'))

    B_test_circles = [ visual.Circle(win, name = str(i),
    radius=conf['QUE_RADIUS'], fillColor=conf['STIM_COLOR'], lineColor=conf['STIM_COLOR'],colorSpace = 'rgb255')
    for i in range(1, 9) ]

    ready_coord(B_test_circles, B_test_texts, "trail\\B_test.yaml", conf)
    # B Trail
    B_texts = []
    for i in range(1, 27):
            text = chr(i//2 + 64) if i % 2 == 0 else str(i//2 + 1)
            B_texts.append(visual.TextStim(win, text = str(text),
            height = conf['QUE_RADIUS'], 
            color = conf['STIM_LETTER_COLOR'],colorSpace = 'rgb255'))

    B_circles = [ visual.Circle(win, name = str(i),
    radius=conf['QUE_RADIUS'], fillColor=conf['STIM_COLOR'], lineColor=conf['STIM_COLOR'],colorSpace = 'rgb255')
    for i in range(1, 27) ]

    ready_coord(B_circles, B_texts, "trail\\B_trail.yaml", conf)

    show_info(win, join('.', 'messages', 'hello.txt'), mouse)
    show_info(win, join('.', 'messages', 'guide.txt'), mouse)

    ## TRAILS 

    # Part A Training
    show_info(win, join('.', 'messages', 'before_training_A.txt'), mouse)    
    core.wait(1)
    run_trial(win, conf, mouse, A_test_circles, A_test_texts, 8, conf['MAX_TEST_TIME'], 'A')

    # Part A
    show_info(win, join('.', 'messages', 'before_test_A.txt'), mouse)
    core.wait(1)
    t = run_trial(win, conf, mouse, A_circles, A_texts, 25, conf['MAX_A_TIME'],'A')
    RESULTS.append([PART_ID, 'part_A', t])

    # Part B Training
    show_info(win, join('.', 'messages', 'before_training_B.txt'), mouse)    
    core.wait(1)
    run_trial(win, conf, mouse, B_test_circles, B_test_texts, 8, conf['MAX_TEST_TIME'], 'B')

    # Part B
    show_info(win, join('.', 'messages', 'before_test_B.txt'), mouse)
    core.wait(1)
    t = run_trial(win, conf, mouse, B_circles, B_texts, 26, conf['MAX_B_TIME'], 'B')
    RESULTS.append([PART_ID, 'part_B', t])

     # === Cleaning time ===
    save_beh_results()
    logging.flush()

    show_info(win, join('.', 'messages', 'end.txt'), mouse)

    win.close()



def run_trial(win, conf, mouse, Circles, Texts, max_num, max_time, part):

    global SQUARE_SIZE
    global RESULTS
    global RESULTS
    cur_stim = 0 # index of current stimuli
    error_mes =  visual.TextStim(win, color='black', text='Nie naciśnięto wlaśćiwego koła', 
    height=28, pos = [0, 0 - (SQUARE_SIZE * 1.12)//2]) # wiadomosc o bledzie
    start_mes = visual.TextStim(win, color='black', text='Aby zacząć eksperyment należy kliknąć kółko z numerem 1', 
    height=28, pos = [0, 0 - (SQUARE_SIZE * 1.12)//2]) # wiadomosc powitalna
    mess_square = visual.Rect(win = win, size = [SQUARE_SIZE * 0.95, SQUARE_SIZE * 0.09], fillColor = 'yellow',pos = [0, 0 - (SQUARE_SIZE * 1.12)//2])
    timer = core.CountdownTimer(0) # timer dla wyswietlania error message
    win.flip()
    # === Start trial ===
    event.clearEvents()
    clock = core.Clock()
    # make sure, that clock will be reset exactly when stimuli will be drawn
    win.callOnFlip(clock.reset)

    while (cur_stim < max_num):      
        # jestli czas uplynal, zakoncz aktualna probe
        if clock.getTime() > max_time:
            return 0 # czas rowny 0 oznacza, ze proba nie zostala ukonczona
        draw_SQUARE(win) # narysuj kwadrat
        # narysuj bodzce od 0 do cur_stim - 1
        for i in range(0, max_num):
            if i < cur_stim:
                # rysowanie lini
                visual.Line(win = win, start = Circles[i].pos, end = Circles[i + 1].pos, lineWidth = conf['LINE_WIDTH'], lineColor = conf['LINE_COLOR']).draw()
            # rysowanie bodzca
            Circles[i].draw()
            Texts[i].draw()
        # narysuj wiadomosc powitalna i zresetuj zegar jesli jestesmy na piewszym kole         
        if cur_stim == 0:
            mess_square.draw()
            start_mes.draw()
            clock.reset()
        # narysuj wiadomosc o bledzie, jesli licznik nie jest wyzerowany
        if timer.getTime() > 0:
            mess_square.draw()
            error_mes.draw()
        win.flip()
         
        buttons, times = mouse.getPressed(getTime=True)
        # sprawdz czy nacisnieto lewy przycisk myszy   
        if buttons[0]:      
            if mouse.isPressedIn(shape = Circles[cur_stim], buttons = [0]):
                # zmien kolor ostatniego nacisnietego bodzca
                Circles[cur_stim].color = conf['STIM_LAST_COLOR']
                # przywroc orginalny kolor poprzedniemu bodzcowi
                if cur_stim - 1 >= 0:
                    Circles[cur_stim - 1].color = conf['STIM_COLOR']
                cur_stim = cur_stim + 1
                # zapisz czas w ktorym nacisnieto kolo
                RESULTS.append([PART_ID, 'Part_' + part + '_point_' + str(cur_stim), clock.getTime()])
                # zresetuj czas myszy
                mouse.clickReset(buttons = [0])
        # jedno nacisniecie jest rejestrowane wiecej niz jeden raz, dlatego sprawdzamy ile minelo od ostatniego klikniecia
            elif times[0] > 0.15:
                timer = core.CountdownTimer(3)

        # wyjscie z eksperymentu
        key = event.getKeys(keyList=['f7','esc'])
        if key == ['f7'] or key == ['esc']:
            abort_with_error(
                'Experiment finished by user on info screen! F7 pressed.')
                
    t = clock.getTime()
    return t

if __name__ == '__main__':
    PART_ID=''
    SCREEN_RES = None
    SQUARE_SIZE = 0.75 # rozmiar kwadratu na ktorym bede wyswietlane bodzce 
    main()

