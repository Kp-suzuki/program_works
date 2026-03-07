from urllib.parse import ParseResultBytes
from xml.dom.pulldom import END_DOCUMENT
from pytmx.util_pygame import load_pygame
import pygame as py
import os
from os.path import join
import random
import numpy as np
import sys
import datetime

# 選択肢後の会話アップデートをする際は次のページへの参照の更新を忘れずに！

dialogue = {'1':("よう、今日は良い天気だな。こんな日は散歩でもしたくなるぜ。","キミもそう思うだろ？",""),
            '2':("Xキーでメニューを開けるぞ",""),
            '3':("禍福は糾える縄の如し......","...........","/","君に、分かるだろうか...",""),
            '4':("これはテストです。","?","はい。","","だからテストだ、って",""),
            '5':("モー",""),
            '6':("を手に入れた！","")}

item_table = {'1':"おいしいリンゴ",'2':"すこし古いメロン"}


SCREEN_SIZE = (800,450)
chara_offset = [0,0,0,0]

dungeon_exit = [(700,240),(10,300)]

#　マップごとの境界
boundary = {'1':[0,SCREEN_SIZE[0] * 100,SCREEN_SIZE[1] * 100,0]}

#　マップごとに、次の行き先を決める
next_dest = [0,2,0,0,0]

map_tmx = '..\\test_game\\map\\map_rpgfuu.tmx' 

path='..\\test_game\\images'
path3 = '..\\test_game\\ipaexg00401'
floor_image = py.image.load(os.path.join(path,'wall.png'))
water_image = py.image.load(os.path.join(path,'water.png'))
fieldimage1 = py.image.load(os.path.join(path,'background1.jpg'))
grass_image = py.image.load(os.path.join(path,'field_grass1.png'))
cursor = py.image.load(os.path.join(path,'cursor.png'))
bed = py.image.load(os.path.join(path,'bed.png'))
enimage = py.image.load(os.path.join(path,'enemy1.png'))

py.font.init()
jfont = py.font.Font(os.path.join(path3,'ipaexg.ttf'),24)

class Character(py.sprite.Sprite): # キャラクターのスプライト
    def __init__(self,pos):
        super().__init__()
        self.image = py.image.load(os.path.join(path,'pig_touka_2.png'))
        self.rect = self.image.get_rect(topleft=pos)
        self.rect_inmap = self.image.get_rect(topleft=(400,225))

        self.xdisp = 0
        self.ydisp = 0
        self.current_pos = np.array(pos)

        self.xvel = 4
        self.yvel = 4

        self.can_talk = False

        self.rect_prev = self.image.get_rect(topleft=pos)


    def move(self,keys,dno):
        d = str(1)

        if keys[py.K_LEFT] and self.rect.left >= boundary[d][0]:
            self.xdisp = -1*self.xvel
        elif keys[py.K_RIGHT] and self.rect.right <= boundary[d][1]:
            self.xdisp = 1*self.xvel
        elif keys[py.K_DOWN] and self.rect.bottom <= boundary[d][2]:
            self.ydisp = 1*self.yvel
        elif keys[py.K_UP] and self.rect.top >= boundary[d][3]:
            self.ydisp = -1*self.yvel
        else:
            self.xdisp = 0
            self.ydisp = 0

    def check_collision(self,sptA,sptB): # どの面がぶつかっているか？
        print(self.rect_prev.top,self.rect_prev.bottom)
        if self.rect_prev.bottom <= sptB.top:
            sptA.bottom = sptB.top
            print("top")
        if self.rect_prev.top >= sptB.bottom:
            sptA.top = sptB.bottom
            print("bottom")
        if self.rect_prev.left >= sptB.right:
            sptA.left = sptB.right
            print("right")
        if self.rect_prev.right <= sptB.left:
            sptA.right = sptB.left
            print("left")

    def make_talkdetection_rect(self): # 会話可能なNPCを判定するためのスプライト
        rect_talk = py.Rect.inflate(self.rect,2,2)
        return rect_talk

    def search_spot(self,item_list): # 調べた地点にアイテムがあれば、そのアイテムの番号と数量を返す
        for items in item_list:
            if items.can_obtain:
                print("you get item!")
                return (items.itemno,1,items.ref_no)
                break
        return [0,0,0]    

    def update(self,screen,keys,dno,npc_group,objects,items,movechar):

        self.rect_prev = py.Rect.copy(self.rect)
        self.rect_talk = self.make_talkdetection_rect()
        if movechar: # キャラを動かせるか？
            self.move(keys,dno)
            self.rect.move_ip(self.xdisp,self.ydisp)

        for sprite in npc_group: # アイテム、NPC、物とぶつかっているか調査      
            if sprite != self and self.rect.colliderect(sprite.rect):
                self.check_collision(self.rect,sprite.rect)
        for sprite in objects:
            if self.rect.colliderect(sprite.rect):
                self.check_collision(self.rect,sprite.rect)
        for sprite in items:
            if self.rect.colliderect(sprite.rect):
                self.check_collision(self.rect,sprite.rect)
        for sprite in npc_group:
            if sprite != self and self.rect_talk.colliderect(sprite.rect):
                sprite.can_talk = True
            else:
                sprite.can_talk = False
        for sprite in items:
            if sprite != self and self.rect_talk.colliderect(sprite.rect):
                sprite.can_obtain = True
            else:
                sprite.can_obtain = False # アイテム取得可能にする

        #print(self.xdisp,self.ydisp) 
        self.current_pos += np.array((self.xdisp, self.ydisp))
        if dno == 0: # マップ上にいるなら中央に、そうでないなら現在地に描写
            screen.blit(self.image,self.rect_inmap)
        else:
            screen.blit(self.image,self.rect)

class NPC(py.sprite.Sprite):
    def __init__(self,npc_no):
        super().__init__() # NPCごとに画像を設定
        if npc_no == 1:
            self.image = py.image.load(os.path.join(path,'npc_tesuto.png')).convert_alpha()
            self.rect = self.image.get_rect(topleft=[200,200])
        elif npc_no == 2:
            self.image = py.image.load(os.path.join(path,'npc2.png')).convert_alpha()
            self.rect = self.image.get_rect(topleft=[400,400])
        elif npc_no == 3:
            self.image = py.image.load(os.path.join(path,'npc3.png')).convert_alpha()
            self.rect = self.image.get_rect(topleft=[250,300])
        elif npc_no == 4:
            self.image = py.image.load(os.path.join(path,'chara2_2.png')).convert_alpha()
            self.rect = self.image.get_rect(topleft=[600,250])
            self.talk_nextpage = [0,1,3]

        self.xdisp = 0
        self.ydisp = 0

        self.can_talk = False
        self.dialogue = dialogue[str(npc_no)]

        self.give_item = 0 # 0 if not giving, item number if giving
    
    def draw(self,screen):
        screen.blit(self.image,self.rect)

class Enemy(py.sprite.Sprite):
    def __init__(self,eno):
        super().__init__()
        self.image = py.image.load(os.path.join(path,'ene1.png')).convert_alpha()
        self.rect = self.image.get_rect(topleft=(225,250))

        self.can_talk = False
        self.dialogue = dialogue[str(eno)]


    def draw(self,screen):
        screen.blit(self.image,self.rect)

class Objects(py.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = bed
        self.rect = self.image.get_rect(topleft=(100,100))

    def draw(self,screen):
        screen.blit(self.image,self.rect)

class Cursor:
    def __init__(self,c_type): # 1:Menu 2:Yes/No
        self.optionno = 1

        if c_type == 1:
            self.cursor_inipos = np.array([20,40])
            self.cursor_disp = np.array([0,40])
            self.noofoption = 5
        elif c_type == 2:
            self.cursor_inipos = np.array([500,225])
            self.cursor_disp = np.array([0,40])
            self.noofoption = 2
        else:
            self.cursor_inipos = np.array([0,0])
            self.cursor_disp = np.array([0,0])

        self.can_move_again = True

    def draw_cursor(self,screen):
        screen.blit(cursor,self.cursor_inipos + self.cursor_disp * (self.optionno - 1))

    def move_cursor(self,keys): # 選択肢の数だけ動かす
        if keys[py.K_DOWN]:
            self.optionno += 1
            self.can_move_again = False
        if keys[py.K_UP]:
            self.optionno -= 1
            self.can_move_again = False
            
        if self.optionno > self.noofoption:
            self.optionno -= 1
        if self.optionno < 1:
            self.optionno += 1

    def remove_cursor(self):
        pass
        
    def update_cursor(self,screen,keys,canmoveagain): # カーソルを動かせるなら、更新
        if canmoveagain:
            self.can_move_again = True
            self.move_cursor(keys)
            
        self.draw_cursor(screen)

class Exit(py.sprite.Sprite): # 出口の機能を持つスプライト
    def __init__(self,dno):
        super().__init__()
        self.image = water_image
        self.rect = self.image.get_rect(topleft=dungeon_exit[dno - 1])

    def draw(self,screen):
        screen.blit(self.image,self.rect)

class Item(py.sprite.Sprite):
    def __init__(self,pos,ino,rno): # rno は落ちているアイテムを識別する固有の番号,inoはアイテムの種類を識別
        super().__init__()
        self.image = py.image.load(os.path.join(path,'item.png')).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

        self.itemno = ino
        self.iname = item_table[str(self.itemno)]
        self.ref_no = rno

        self.can_obtain = False

    def show_item(self,screen):
        screen.blit(self.image,self.rect)

class Dungeon:
    def __init__(self,dno):
        self.exitmark = Exit(dno)
        self.dungeon_no = dno

        self.start_battle = False

        self.outof_dungeon = False

        self.allmap = py.sprite.Group()
        self.maps = {'world':load_pygame(map_tmx)} # ワールドマップの情報を得る
        
        for x, y, surf in self.maps['world'].get_layer_by_name('Terrain').tiles():
            Mapchip((x * 32, y * 32), surf, self.allmap)

        self.dungeon_npc = py.sprite.RenderUpdates()
        self.dungeon_objects =  py.sprite.RenderUpdates() # それぞれのグループを作成
        self.dungeon_items =  py.sprite.RenderUpdates()

        if dno == 1:
            N1 = NPC(1)
            N2 = NPC(2)
            N3 = NPC(3)
            revive = Item([300,200],2,1) # item = (pos,ino,rno)
            self.dungeon_items.add(revive)
            self.dungeon_npc.add(N1,N2,N3)
        if dno == 2:
            N4 = NPC(4)
            E1 = Enemy(5)
            bed = Objects()
            potion = Item([100,300],1,1) # ダンジョンに情報を入れ、グループを作る
            self.dungeon_objects.add(bed)
            self.dungeon_items.add(potion)
            self.dungeon_npc.add(N4,E1)

    def draw_dungeon(self,screen): # ダンジョンを描画
        if self.dungeon_no == 1:
            for x in range(0,round(SCREEN_SIZE[0] / 32)):
                for y in range(0,round(SCREEN_SIZE[1] / 32)):                            
                    screen.blit(floor_image,(x * 32, y * 32))
            screen.blit(jfont.render("spaceキーで物や人を調べられます",False,'white','black'),(10,10))
        if self.dungeon_no == 2:
            for x in range(0,round(SCREEN_SIZE[0] / 32)):
                for y in range(0,round(SCREEN_SIZE[1] / 32)):                            
                    screen.blit(grass_image,(x * 32, y * 32))
        self.exitmark.draw(screen)

    def draw_map(self,screen,chara):
        
        gchor = [chara.current_pos[0], chara.current_pos[1]]
        print(gchor)

        for map_chip in self.allmap:
            # if (map_chip.x >= gchor[0] - SCREEN_SIZE[0] // 2 and map_chip.x <= gchor[0] + SCREEN_SIZE[0] // 2) and (map_chip.y <= gchor[1] + SCREEN_SIZE[1] // 2 and map_chip.y >= gchor[1] - SCREEN_SIZE[1] // 2):
            map_chip.draw(screen,chara)

    def draw_charas(self,screen):
        for charas in self.dungeon_npc:
            charas.draw(screen)

    def put_items(self,screen):
        for items in self.dungeon_items: # それぞれの物を画面におく
            items.show_item(screen)

    def put_objects(self,screen):
        for obj in self.dungeon_objects:
            obj.draw(screen)
    
    def remove_item(self,iteminfo): # 取ったアイテムを消す
        for items in self.dungeon_items:
            if items.ref_no == iteminfo[2]:
                items.remove(self.dungeon_items)

        
    def out_of_dungeon(self,chara): # 出口とぶつかったら、ダンジョンの外へ
        if py.sprite.collide_rect(self.exitmark,chara):
            self.dungeon_no = next_dest[self.dungeon_no]
            self.outof_dungeon = True
        else:
            self.outof_dungeon = False

    def generate_dungeon(self,screen,chara): # ダンジョンを生成
        self.out_of_dungeon(chara)
        if self.dungeon_no == 0:
            self.draw_map(screen,chara)
        else:
            self.draw_dungeon(screen)
        self.put_objects(screen)
        self.draw_charas(screen)
        self.put_items(screen)
        
class Talk:
    def __init__(self):
        self.is_talking = False
        self.next_page = False
        self.talk_cont = 0
        self.talk_branch = 0
        self.txt_disp = [py.surface.Surface((0,0)),py.surface.Surface((0,0))]
        self.canpressagain = True

        self.battle_flag = False
        self.show_option = False

    def text_reset(self):
        self.txt_disp = [py.surface.Surface((0,0)),py.surface.Surface((0,0))]

    def show_message(self,got_item,show):
        txtno = 0
        # print('hello')
        
        if show:
            self.is_talking = True
            while dialogue['6'][txtno] != "":
                self.txt_disp[txtno] = jfont.render(str(item_table[str(got_item[0])]) + dialogue['6'][txtno],False,'white','black')
                txtno += 1




    def update(self,group,op_no,choose):# 会話を行う
        txtno = 0
        if self.next_page:
            self.text_reset()

        if self.is_talking and not self.next_page: # もし最後のページなら、終了
            self.is_talking = False
            self.text_reset()
        else:
            for sprites in group:
                if sprites.can_talk:
                    if type(sprites) == Enemy:
                        self.battle_flag = True
                    else:
                        self.battle_flag = False
                    if choose: # 選択肢で選んだなら、選んだ場所へ飛ぶ
                        print("eeeeeeeeee")
                        txtno += sprites.talk_nextpage[op_no]
                        self.talk_cont = self.talk_branch + sprites.talk_nextpage[op_no]
                        print(self.talk_cont)
                        txtno = 0
                        self.show_option = False

                    while sprites.dialogue[self.talk_cont + txtno] != "" and sprites.dialogue[self.talk_cont + txtno] != "?": # もし分岐や終点でないなら、
                        if sprites.dialogue[self.talk_cont + txtno] != "/": # ページの終わりまで、
                            self.txt_disp[txtno] = jfont.render(sprites.dialogue[self.talk_cont + txtno],False,'white','black')
                            print(sprites.dialogue[self.talk_cont + txtno])
                            txtno += 1
                        else: # そうでないなら次のページへ
                            self.next_page = True
                            self.talk_cont = txtno + 1
                            txtno = 0
                            break
                    if sprites.dialogue[self.talk_cont + txtno] == "?": # 分岐へ来たら、選択肢を見せる
                        self.talk_branch = self.talk_cont + txtno
                        # 選択した会話に進む方法を考える。
                        self.show_option = True
                        self.next_page = True
                    if sprites.dialogue[self.talk_cont + txtno] == "": # 終点へ来たら、終了
                        self.talk_cont = 0
                        self.next_page = False
                    self.is_talking = True
                    self.canpressagain = False

class Background:
    def __init__(self):
        pass

    def draw_dbox(screen):
        py.draw.rect(screen,'white',(10,300,700,80))

    def draw_optionbox(screen):
        py.draw.rect(screen,'white',(550,225,75,60))

class Menu:
    def __init__(self):
        self.menu_open = False
        self.canpress_again = False

    def show_menu(self,screen,gt):

        py.draw.rect(screen,'white',(10,10,700,350))

        screen.blit(jfont.render("Status",False,'white','black'),(40,40))

        screen.blit(jfont.render("Item",False,'white','black'),(40,80))

        screen.blit(jfont.render("Ability",False,'white','black'),(40,120))

        screen.blit(jfont.render("Settings",False,'white','black'),(40,160))

        screen.blit(jfont.render("Time : " + str(datetime.timedelta(seconds = int(gt / 1000))),False,'white','black'),(40,200))

    def switch_menu(self): # メニューの開閉を制御
        self.menu_open = not self.menu_open
        self.canpress_again = False

class Mapchip(py.sprite.Sprite):
    def __init__(self,pos,surf,group):
        super().__init__(group)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)

        self.x = pos[0]
        self.y = pos[1]

    def draw(self,screen,char):
        offset = -1 * (char.current_pos) 
        screen.blit(self.image,self.rect.topleft + offset)

class Item_box:
    def __init__(self):
        self.no_of_item = 0
        self.itemlist = np.empty([0,0])

    def add_item(self,item_no,numofitem): # アイテムを追加
        itemlist_temp = self.itemlist.tolist()
        itemlist_temp.append([item_no,numofitem])
        self.itemlist = np.asarray(itemlist_temp)
        self.no_of_item += 1
        

    def showitem(self):
        if len(self.itemlist) == 0:
            print("You have no items...")
        else:
            for i in range(0,self.no_of_item):
                # print(self.itemlist[i][0],self.itemlist[i][1])
                print(item_table[str(self.itemlist[i][0])] + " × " + str(self.itemlist[i][1]) )

class Game:
    def __init__(self):
        py.init()
        self.screen = py.display.set_mode(SCREEN_SIZE)
        self.clock = py.time.Clock()
        self.game_time = 0
        self.movechar = True

        self.option_no = 0
        self.is_choosing = False
        self.get_something = [0,0]
        self.showing_message = False

        self.dungeon_no = 1
        self.enter_dungeon = False

        self.can_press_again = True

        self.moving_cursor = False
        self.can_move_cursor_again = True
        self.press_to_progress = False

        self.is_battle = False
        self.battle_flag = False

    def run(self):
        C = Character([SCREEN_SIZE[0] / 2,SCREEN_SIZE[1] / 2])
        talk = Talk()
        menu = Menu() 
        items = Item_box()
        dungeon = Dungeon(self.dungeon_no) #    必要なインスタンスを生成
            
        while True:
            self.screen.fill('blue')
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()
                
                if event.type == py.KEYUP: # キーを上げると、再び押せるようになる
                    print('hi')
                    self.can_press_again = True
                    self.can_move_cursor_again = True

            keys = py.key.get_pressed() # 入力を獲得

            if self.is_battle:
                print('battle!')

            if self.enter_dungeon:
                dungeon = Dungeon(self.dungeon_no) # ダンジョンに入ったら、ダンジョン生成
                self.enter_dungeon = False 

            dungeon.generate_dungeon(self.screen,C)

            if keys[py.K_SPACE] and self.can_press_again: # スペースを押すと、
                if talk.show_option: # オプションを見せているなら、選んだオプションを記録
                    self.option_no = cursor.optionno
                    talk.show_option = False
                    self.is_choosing = True
                    self.moving_cursor = False
                else:
                    self.is_choosing = False
                if self.showing_message: # 獲得メッセージを見せているなら進める、そうでないなら調べる
                    self.showing_message = False
                    dungeon.remove_item(self.get_something) # アイテムを除去
                    self.get_something = [0,0]
                else:
                    self.get_something = C.search_spot(dungeon.dungeon_items)
                    if self.get_something[0] != 0:
                        talk.canpressagain = False
                talk.update(dungeon.dungeon_npc,self.option_no,self.is_choosing) # 会話をアップデート
                
                
                if not talk.canpressagain:  # talk.canpressagainにより、会話を出す際はキーを上げるまで反応しないようにする
                    self.can_press_again = False

            if keys[py.K_x] and self.can_press_again: # メニューを見る
                print("okay")
                menu.switch_menu()
                if menu.menu_open:
                    self.moving_cursor = True
                    cursor = Cursor(1)
                else:
                    self.moving_cursor = False
                if not menu.canpress_again:
                    self.can_press_again = False

            if keys[py.K_z] and self.can_press_again: # 取っているアイテムを見せる
                items.showitem()

            if menu.menu_open:
                menu.show_menu(self.screen,self.game_time)

            # if self.moving_cursor:
            #     cursor.update_cursor(self.screen,keys,self.can_move_cursor_again)
            #     self.can_move_cursor_again = cursor.can_move_again
            # elif not self.moving_cursor:
            #     C.update(self.screen,keys,dungeon.dungeon_no,dungeon.dungeon_npc,dungeon.dungeon_objects)

            if dungeon.outof_dungeon: # ダンジョンを出た場合、
                self.dungeon_no = next_dest[self.dungeon_no]
                self.enter_dungeon = True

            if talk.show_option: # 選択肢を見せるなら、
                # print("showing option")
                Background.draw_optionbox(self.screen)
                self.screen.blit(jfont.render("はい",False,'white','black'),(575,240))
                self.screen.blit(jfont.render("はい？",False,'white','black'),(575,270))
                if not self.moving_cursor:
                    self.moving_cursor = True
                    cursor = Cursor(2)
                self.option_no = cursor.optionno

            # if talk.battle_flag and not talk.is_talking:
            #     self.is_battle = True

            if self.moving_cursor: # カーソルを動かしているなら、キャラを動かさないように
                self.movechar = False
                cursor.update_cursor(self.screen,keys,self.can_move_cursor_again)
                self.can_move_cursor_again = cursor.can_move_again
            elif not self.moving_cursor:
                self.movechar = True

            if not menu.menu_open: # メニューが開いていないなら、キャラの情報を更新
                C.update(self.screen,keys,dungeon.dungeon_no,dungeon.dungeon_npc,dungeon.dungeon_objects,dungeon.dungeon_items,self.movechar)
            
            if self.get_something[0] != 0: # 何か獲得したなら、メッセージを表示
                items.add_item(self.get_something[0],1)
                self.showing_message = True
                talk.show_message(self.get_something,self.showing_message)
                # dungeon.dungeon_items

            if talk.is_talking: #  会話中ならテキストボックスを生成
                # print("hi")
                Background.draw_dbox(self.screen)
                self.screen.blit(talk.txt_disp[0],(10,320))
                self.screen.blit(talk.txt_disp[1],(10,350))
                        
            py.display.update() # 出力を1秒に60回リフレッシュ
            self.game_time += self.clock.tick(60)

if __name__ == '__main__':
    game = Game()
    game.run()