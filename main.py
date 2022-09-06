import atexit
import codecs
import csv
import random
from os.path import join
from statistics import mean

import yaml
from psychopy import visual, event, logging, gui, core, colors

from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product

def ready_coord(Table, Text, filename, conf):
    global SQUARE_SIZE
    global SCREEN_RES
    offset_x = SQUARE_SIZE / 2
    offset_y = SQUARE_SIZE / 2
    points = yaml.safe_load(open(filename, encoding='utf-8'))
    map_size = points['MAP_SIZE'] - 1
    n = points['POINTS']
    for i in range(1, n + 1):
        new_pos = []
        new_pos = points["POINT_" + str(i)]
        new_pos[0] = (int)((new_pos[0] / map_size) * SQUARE_SIZE) - offset_x - conf["QUE_RADIUS"]/8
        new_pos[1] = (int)((new_pos[1] / map_size) * SQUARE_SIZE) - offset_y - conf["QUE_RADIUS"]/8
        Table[i - 1].pos = new_pos
        Text[i - 1].pos = new_pos
    
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


def show_image(win, file_name, size, key='f7'):
    """
    Show instructions in a form of an image.
    """
    image = visual.ImageStim(win=win, image=file_name,
                             interpolate=True, size=size)
    image.draw()
    win.flip()
    clicked = event.waitKeys(keyList=[key, 'return', 'space'])
    if clicked == [key]:
        logging.critical(
            'Experiment finished by user! {} pressed.'.format(key[0]))
        exit(0)
    win.flip()


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


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='white', text=msg,
                          height=20, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(maxWait = 10, keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
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
    SCREEN_RES = get_screen_res()
    print(SCREEN_RES)
    SQUARE_SIZE = SQUARE_SIZE * SCREEN_RES.get("height")
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
            text = chr(i//2 + 64) if i % 2 == 0 else str(i)
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
            text = chr(i//2 + 64) if i % 2 == 0 else str(i)
            B_texts.append(visual.TextStim(win, text = str(text),
            height = conf['QUE_RADIUS'], 
            color = conf['STIM_LETTER_COLOR'],colorSpace = 'rgb255'))

    B_circles = [ visual.Circle(win, name = str(i),
    radius=conf['QUE_RADIUS'], fillColor=conf['STIM_COLOR'], lineColor=conf['STIM_COLOR'],colorSpace = 'rgb255')
    for i in range(1, 27) ]

    ready_coord(B_circles, B_texts, "trail\\B_trail.yaml", conf)

    show_info(win, join('.', 'messages', 'hello.txt'))
    show_info(win, join('.', 'messages', 'guide.txt'))

    ## TRAILS 

    # Part A Training
    show_info(win, join('.', 'messages', 'before_training_A.txt'))    
    core.wait(1)
    run_trial(win, conf, mouse, A_test_circles, A_test_texts, 8, conf['MAX_TEST_TIME'])

    # Part A
    show_info(win, join('.', 'messages', 'before_test_A.txt'))
    core.wait(1)
    t = run_trial(win, conf, mouse, A_circles, A_texts, 25, conf['MAX_A_TIME'])
    RESULTS.append([PART_ID, 'part_A', t])

    # Part B Training
    show_info(win, join('.', 'messages', 'before_training_B.txt'))    
    core.wait(1)
    run_trial(win, conf, mouse, B_test_circles, B_test_texts, 8, conf['MAX_TEST_TIME'])

    # Part B
    show_info(win, join('.', 'messages', 'before_test_B.txt'))
    core.wait(1)
    t = run_trial(win, conf, mouse, B_circles, B_texts, 26, conf['MAX_B_TIME'])
    RESULTS.append([PART_ID, 'part_B', t])

     # === Cleaning time ===
    save_beh_results()
    logging.flush()

    show_info(win, join('.', 'messages', 'end.txt'))

    win.close()



def run_trial(win, conf, mouse, Circles, Texts, max_num, max_time):

    global SQUARE_SIZE
    cur_stim = 0 # index of current stimuli
    #error_mes =  visual.TextStim(win, color='black', text='Naciśnięto blędne koło', 
    #height=20, pos = [0, 0]) # wiadomosc o bledzie
    start_mes = visual.TextStim(win, color='white', text='Aby zacząć eksperyment należy kliknij kółko z numerem 1', 
    height=20, pos = [0, 0 - (SQUARE_SIZE * 1.1)//2]) # wiadomosc powitalna
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
        draw_SQUARE(win)
        # narysuj bodzce od 0 do cur_stim - 1
        for i in range(0, cur_stim):
            # rysowanie lini
            visual.Line(win = win, start = Circles[i].pos, end = Circles[i + 1].pos, lineWidth = conf['LINE_WIDTH'], lineColor = conf['LINE_COLOR']).draw()
            # rysowanie bodzca
            Circles[i].draw()
            Texts[i].draw()    
        # narysuj aktualny bodziec     
        Circles[cur_stim].draw()
        Texts[cur_stim].draw() 
        if cur_stim == 0:
            start_mes.draw()
        win.flip()
        # sprawdz czy nacisnieto poprawne kolko    
        if mouse.isPressedIn(shape = Circles[cur_stim], buttons = [0]):
            # zmien kolor ostatniego nacisnietego bodzca
            Circles[cur_stim].color = conf['STIM_LAST_COLOR']
            # przywroc orginalny kolor poprzedniemu bodzcowi
            if cur_stim - 1 >= 0:
                Circles[cur_stim - 1].color = conf['STIM_COLOR']
            cur_stim = cur_stim + 1
            mouse.clickReset(buttons = [0])
                

                


    t = clock.getTime()
    return t

    return key_pressed, rt  # return all data collected during trial

if __name__ == '__main__':
    PART_ID=''
    SCREEN_RES = None
    SQUARE_SIZE = 0.7
    main()


''' if not reaction:  # no reaction during stim time, allow to answer after that
    question_frame.draw()
    question_label.draw()
    win.flip()
    reaction=event.waitKeys(keyList=list(
        conf['REACTION_KEYS']), maxWait=conf['REACTION_TIME'], timeStamped=clock)'''
