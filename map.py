import sys
import os
import sqlite3
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import (QApplication, QHBoxLayout,
                             QPushButton, QVBoxLayout, 
                             QWidget, QLabel,
                             QRadioButton,)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

file='mz.db'

# geoplace=(60, 30.5)
geoplace=(52.95, 55.95)

class MapWidget(QWidget):
    """Виджет для вывода карты
            x-lon, y-lat"""
    def __init__(self):
        super().__init__()

    def showWidget(self,  myplace, filename, r=0.05):
        self.bbox = (myplace[0]-r, 
                     myplace[1]-r, 
                     myplace[0]+r, 
                     myplace[1]+r)
        self.points = list()
        # Создаем объект графики
        fig = Figure(figsize=(10, 10), dpi=60)
        fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
        self.ax = fig.add_subplot(111)
        self.ax2 = fig.add_subplot(111, zorder=1)
        self.ax3 = fig.add_subplot(111, zorder=2)
        # координаты с картой
        self.set_size(self.ax)
        # координы для дрона
        self.set_size(self.ax2, True)
        # координы для маршрута
        self.set_size(self.ax3, True)
        # Создаем объект Canvas
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Создаем кнопки
        self.clear_points_btn = QPushButton('Очистить точки', self)     
        self.send_points_btn = QPushButton('Отправить точки', self)
        self.radio_button = QRadioButton('Маршрут', self)
        self.radio_button.setChecked(False)
        # создаем вид виджета
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.toolbar)
        mainlayout.addWidget(self.canvas)
        sublayout = QHBoxLayout()
        sublayout.addWidget(self.radio_button)
        sublayout.addWidget(self.clear_points_btn)
        sublayout.addWidget(self.send_points_btn)
        mainlayout.addLayout(sublayout)
        self.setLayout(mainlayout)
        #обращаемся к базе данных
        if os.path.exists(filename):
            self.con = sqlite3.connect(filename)
            self.cur = self.con.cursor()
            print('initialized db')
        else:
            raise FileNotFoundError(f"File {filename} not found.")
        # рисуем карту с точками
        self.ax.scatter(myplace[1], 
                        myplace[0], 
                        s=5, 
                        c='red', 
                        marker='o')
        self.rc = self.ax2.plot(  myplace[1], 
                                    myplace[0], 
                                    marker='o')
        self.draw_way(myplace, r, (
            # ('highway','pink',1 , True, False),
            # ('building','black', 1, False, True),
            # ('wood', 'green', 1, True, True),
            # ('railway', 'red', 1, True, False),
            # ('waterway=river', 'blue', 1, True, False),
            # ('waterway=canal', 'blue', 1, True, False),
            # ('natural=water', 'blue', 1, True, True),
        # ))
            ('highway=trunk','pink', 4, True, False),
            ('highway=tertiary','pink', 2, True, False),
            ('highway=secondary','pink', 3, True, False),
            ('highway=residential','gray', 1, True, False),
            ('highway=service','gray', 1, True, False),
            ('highway=unclassified','gray', 1, True, False),
            ('building','black', 1, False, True),
            ('waterway=river', 'blue', 1, True, False),
            ('waterway=canal', 'blue', 1, True, False),
            ('natural=water', 'blue', 1, True, True),
            ('wood', 'green', 1, True, True),
            ('railway', 'red', 1, True, False),
        ))
        # закрываем бд
        self.con.close()
        # конектим сигналы к слотам
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.clear_points_btn.clicked.connect(self.clear_points)
        self.send_points_btn.clicked.connect(self.send_points)


    def set_size(self, graph, alpha=False):
        """
        Функция для установки размера карты
        """
        graph.set_xlim(self.bbox[1], self.bbox[3])
        graph.set_ylim(self.bbox[0], self.bbox[2])
        graph.set_aspect((self.bbox[2]-self.bbox[0])/(self.bbox[3]-self.bbox[1]))
        if alpha:
            graph.patch.set_alpha(0)
    

    def draw_way(self, place, r,  ways):
        """
        Функция для рисования карты
        """
        # Рисуем структуры
        for type, color, linewidth, plot, fill in ways:
            self.cur.execute(f'''
                    SELECT loc FROM ways
                    WHERE tag LIKE "%{type}%"''')
            # для каждой структуры находим точки и рисуем
            for loc in self.cur.fetchall():
                loc = loc[0].split(';')
                x = list()
                y = list()
                for i in loc:
                    lat, lon = i[1:-1].split(', ')
                    lat = float(lat)
                    lon = float(lon)
                    if not (lat<place[0]-r or lat>place[0]+r or lon<place[1]-r or lon>place[1]+r):
                        x.append(lon)
                        y.append(lat)
                if plot:
                    self.ax.plot(x, y, color, linewidth=linewidth)
                if fill:
                    self.ax.fill(x, y, color, alpha=0.4)
    

    def move_rc(self, new_x, new_y):
        """
        Функция для перемещения дрона на графике
        """
        # удаляем старую точку
        self.rc.remove()

        # создаем новую точку с новыми координатами
        self.rc = self.ax2.plot(new_x, new_y, marker='o')

        # обновляем график
        self.canvas.draw()

    def on_click(self, event):
        """
        Функция для рисования пути на карте
        """
        if self.radio_button.isChecked():
            # Получаем координаты точки
            x, y = event.xdata, event.ydata
            # Рисуем точку
            self.ax3.plot(x, y, 'o', color='blue')
            # Добавляем точку в список
            self.points.append((x, y))
            # Если у нас больше одной точки, соединяем их линией
            if len(self.points) > 1:
                x, y = zip(*self.points)
                self.ax3.plot(x, y, '-', color='blue')
            # Обновляем график
            self.canvas.draw()
    
    def clear_points(self):
        """
        Функция для очищения пути
        """
        # Очищаем массив с координатами точек и 
        self.points = list()
        self.ax3.cla()
        # Перерисовываем график
        self.set_size(self.ax3, True)
        self.canvas.draw()

    def send_points(self):
        pass

    


            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapWidget()
    window.showWidget(geoplace, file, 0.05)
    window.show()
    sys.exit(app.exec_())
