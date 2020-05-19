from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from random import randrange
import atlaselectrophysiology.load_data as ld
import atlaselectrophysiology.plot_data as pd
import atlaselectrophysiology.ColorBar as cb
import atlaselectrophysiology.ephys_gui_setup as ephys_gui


class MainWindow(QtWidgets.QMainWindow, ephys_gui.Setup):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.init_variables()
        self.init_layout(self)
        self.loaddata = ld.LoadData(self.max_idx)
        self.populate_lists(self.loaddata.get_subjects(), self.subj_list, self.subj_combobox)
        self.configure = True

    def init_variables(self):
        """
        Initialise variables
        """
        # Line styles and fonts
        self.kpen_dot = pg.mkPen(color='k', style=QtCore.Qt.DotLine, width=2)
        self.rpen_dot = pg.mkPen(color='r', style=QtCore.Qt.DotLine, width=2)
        self.kpen_solid = pg.mkPen(color='k', style=QtCore.Qt.SolidLine, width=2)
        self.bpen_solid = pg.mkPen(color='b', style=QtCore.Qt.SolidLine, width=3)
        self.bar_colour = QtGui.QColor(160, 160, 160)

        # Padding to add to figures to make sure always same size viewbox
        self.pad = 0.05

        # Variables to do with probe dimension
        self.probe_tip = 0
        self.probe_top = 3840
        self.probe_extra = 100
        self.view_total = [-2000, 6000]
        self.depth = np.arange(self.view_total[0], self.view_total[1], 20)
        self.extend_feature = 5000 / 1e6

        # Initialise with linear fit scaling as default
        self.lin_fit = True

        # Variables to keep track of number of fits (max 10)
        self.max_idx = 10
        self.idx = 0
        self.current_idx = 0
        self.total_idx = 0
        self.last_idx = 0
        self.diff_idx = 0

        # Variables to keep track of reference lines and points added
        self.line_status = True
        self.label_status = True
        self.lines_features = np.empty((0, 3))
        self.lines_tracks = np.empty((0, 1))
        self.points = np.empty((0, 1))
        self.scale = 1

        # Variables to keep track of plots and colorbars
        self.img_plots = []
        self.line_plots = []
        self.probe_plots = []
        self.img_cbars = []
        self.probe_cbars = []
        self.scale_regions = np.empty((0, 1))

        # Variables to keep track of popup plots
        self.cluster_popups = []
        self.popup_status = True

    def set_axis(self, fig, ax, show=True, label=None, pen='k', ticks=True):
        """
        Show/hide and configure axis of figure
        :param fig: figure associated with axis
        :type fig: pyqtgraph PlotWidget
        :param ax: orientation of axis, must be one of 'left', 'right', 'top' or 'bottom'
        :type ax: string
        :param show: 'True' to show axis, 'False' to hide axis
        :type show: bool
        :param label: axis label
        :type label: string
        :parm pen: colour on axis
        :type pen: string
        :param ticks: 'True' to show axis ticks, 'False' to hide axis ticks
        :param ticks: bool
        :return axis: axis object
        :type axis: pyqtgraph AxisItem
        """
        if not label:
            label = ''
        if type(fig) == pg.PlotItem:
            axis = fig.getAxis(ax)
        else:
            axis = fig.plotItem.getAxis(ax)
        if show:
            axis.show()
            axis.setPen(pen)
            axis.setLabel(label)
            if not ticks:
                axis.setTicks([[(0, ''), (0.5, ''), (1, '')]])
        else:
            axis.hide()

        return axis

    def populate_lists(self, data, list_name, combobox):
        """
        Populate drop down lists with subject/session options
        :param data: list of options to add to widget
        :type data: 1D array of strings
        :param list_name: widget object to which to add data to
        :type list_name: QtGui.QStandardItemModel
        :param combobox: combobox object to which to add data to
        :type combobox: QtWidgets.QComboBox
        """
        for dat in data:
            item = QtGui.QStandardItem(dat)
            item.setEditable(False)
            list_name.appendRow(item)

        combobox.setCurrentIndex(0)

    def set_view(self, view=1, configure=False):
        """
        Layout of ephys data figures, can be changed using Shift+1, Shift+2, Shift+3
        :param view: from left to right
            1: img plot, line plot, probe plot
            2: img plot, probe plot, line plot
            3: probe plot, line plot, img_plot
        :type view: int
        :param configure: Returns the width of each image, set to 'True' once during the setup to
                          ensure figures are always the same width
        :type configure: bool
        """
        if configure:
            self.fig_ax_width = self.fig_data_ax.width()
            self.fig_img_width = self.fig_img.width() - self.fig_ax_width
            self.fig_line_width = self.fig_line.width()
            self.fig_probe_width = self.fig_probe.width()

        if view == 1:
            self.fig_data_layout.removeItem(self.fig_img_cb)
            self.fig_data_layout.removeItem(self.fig_probe_cb)
            self.fig_data_layout.removeItem(self.fig_img)
            self.fig_data_layout.removeItem(self.fig_line)
            self.fig_data_layout.removeItem(self.fig_probe)
            self.fig_data_layout.addItem(self.fig_img_cb, 0, 0)
            self.fig_data_layout.addItem(self.fig_probe_cb, 0, 1, 1, 2)
            self.fig_data_layout.addItem(self.fig_img, 1, 0)
            self.fig_data_layout.addItem(self.fig_line, 1, 1)
            self.fig_data_layout.addItem(self.fig_probe, 1, 2)

            self.set_axis(self.fig_img_cb, 'left', pen='w')
            self.set_axis(self.fig_probe_cb, 'left', show=False)
            self.set_axis(self.fig_img, 'left', label='Distance from probe tip (uV)')
            self.set_axis(self.fig_probe, 'left', show=False)
            self.set_axis(self.fig_line, 'left', show=False)

            self.fig_img.setPreferredWidth(self.fig_img_width + self.fig_ax_width)
            self.fig_line.setPreferredWidth(self.fig_line_width)
            self.fig_probe.setFixedWidth(self.fig_probe_width)

            self.fig_data_layout.layout.setColumnStretchFactor(0, 6)
            self.fig_data_layout.layout.setColumnStretchFactor(1, 2)
            self.fig_data_layout.layout.setColumnStretchFactor(2, 1)
            self.fig_data_layout.layout.setRowStretchFactor(0, 1)
            self.fig_data_layout.layout.setRowStretchFactor(1, 10)

            self.fig_img.update()
            self.fig_line.update()
            self.fig_probe.update()

        if view == 2:
            self.fig_data_layout.removeItem(self.fig_img_cb)
            self.fig_data_layout.removeItem(self.fig_probe_cb)
            self.fig_data_layout.removeItem(self.fig_img)
            self.fig_data_layout.removeItem(self.fig_line)
            self.fig_data_layout.removeItem(self.fig_probe)
            self.fig_data_layout.addItem(self.fig_img_cb, 0, 0)

            self.fig_data_layout.addItem(self.fig_probe_cb, 0, 1, 1, 2)
            self.fig_data_layout.addItem(self.fig_img, 1, 0)
            self.fig_data_layout.addItem(self.fig_probe, 1, 1)
            self.fig_data_layout.addItem(self.fig_line, 1, 2)

            self.set_axis(self.fig_img_cb, 'left', pen='w')
            self.set_axis(self.fig_probe_cb, 'left', show=False)
            self.set_axis(self.fig_img, 'left', label='Distance from probe tip (uV)')
            self.set_axis(self.fig_probe, 'left', show=False)
            self.set_axis(self.fig_line, 'left', show=False)

            self.fig_img.setPreferredWidth(self.fig_img_width + self.fig_ax_width)
            self.fig_line.setPreferredWidth(self.fig_line_width)
            self.fig_probe.setFixedWidth(self.fig_probe_width)

            self.fig_data_layout.layout.setColumnStretchFactor(0, 6)
            self.fig_data_layout.layout.setColumnStretchFactor(1, 1)
            self.fig_data_layout.layout.setColumnStretchFactor(2, 2)
            self.fig_data_layout.layout.setRowStretchFactor(0, 1)
            self.fig_data_layout.layout.setRowStretchFactor(1, 10)

            self.fig_img.update()
            self.fig_line.update()
            self.fig_probe.update()

        if view == 3:
            self.fig_data_layout.removeItem(self.fig_img_cb)
            self.fig_data_layout.removeItem(self.fig_probe_cb)
            self.fig_data_layout.removeItem(self.fig_img)
            self.fig_data_layout.removeItem(self.fig_line)
            self.fig_data_layout.removeItem(self.fig_probe)
            self.fig_data_layout.addItem(self.fig_probe_cb, 0, 0, 1, 2)
            self.fig_data_layout.addItem(self.fig_img_cb, 0, 2)
            self.fig_data_layout.addItem(self.fig_probe, 1, 0)
            self.fig_data_layout.addItem(self.fig_line, 1, 1)
            self.fig_data_layout.addItem(self.fig_img, 1, 2)

            self.set_axis(self.fig_probe_cb, 'left', pen='w')
            self.set_axis(self.fig_img_cb, 'left', show=False)
            self.set_axis(self.fig_line, 'left', show=False)
            self.set_axis(self.fig_img, 'left', pen='w')
            self.set_axis(self.fig_img, 'left', show=False)
            self.set_axis(self.fig_probe, 'left', label='Distance from probe tip (uV)')

            self.fig_data_layout.layout.setColumnStretchFactor(0, 1)
            self.fig_data_layout.layout.setColumnStretchFactor(1, 2)
            self.fig_data_layout.layout.setColumnStretchFactor(2, 6)
            self.fig_data_layout.layout.setRowStretchFactor(0, 1)
            self.fig_data_layout.layout.setRowStretchFactor(1, 10)

            self.fig_probe.setFixedWidth(self.fig_probe_width + self.fig_ax_width)
            self.fig_img.setPreferredWidth(self.fig_img_width)
            self.fig_line.setPreferredWidth(self.fig_line_width)

            self.fig_img.update()
            self.fig_line.update()
            self.fig_probe.update()

    def toggle_plots(self, options_group):
        """
        Allows user to toggle through image, line and probe plots using keyboard shortcuts Alt+1,
        Alt+2 and Alt+3 respectively
        :param options_group: Set of plots to toggle through
        :type options_group: QtGui.QActionGroup
        """

        current_act = options_group.checkedAction()
        actions = options_group.actions()
        current_idx = [iA for iA, act in enumerate(actions) if act == current_act][0]
        next_idx = np.mod(current_idx + 1, len(actions))
        actions[next_idx].setChecked(True)
        actions[next_idx].trigger()

    """
    Plot functions
    """

    def plot_histology(self, fig, ax='left', movable=True):
        """
        Plots histology figure - brain regions that intersect with probe track
        :param fig: figure on which to plot
        :type fig: pyqtgraph PlotWidget
        :param ax: orientation of axis, must be one of 'left' (fig_hist) or 'right' (fig_hist_ref)
        :type ax: string
        :param movable: whether probe reference lines can be moved, True for fig_hist, False for
                        fig_hist_ref
        :type movable: Bool
        """
        fig.clear()
        axis = fig.getAxis(ax)
        axis.setTicks([self.loaddata.hist_data['axis_label'][self.idx]])
        axis.setZValue(10)

        # Plot each histology region
        for ir, reg in enumerate(self.loaddata.hist_data['region'][self.idx]):
            colour = QtGui.QColor(*self.loaddata.hist_data['colour'][self.idx][ir])
            region = pg.LinearRegionItem(values=(reg[0], reg[1]),
                                         orientation=pg.LinearRegionItem.Horizontal,
                                         brush=colour, movable=False)
            bound = pg.InfiniteLine(pos=reg[0], angle=0, pen='w')
            fig.addItem(region)
            fig.addItem(bound)

        bound = pg.InfiniteLine(pos=self.loaddata.hist_data['region'][self.idx][-1][1], angle=0,
                                pen='w')
        fig.addItem(bound)
        # Add dotted lines to plot to indicate region along probe track where electrode
        # channels are distributed
        self.tip_pos = pg.InfiniteLine(pos=self.probe_tip, angle=0, pen=self.kpen_dot,
                                       movable=movable)
        self.top_pos = pg.InfiniteLine(pos=self.probe_top, angle=0, pen=self.kpen_dot,
                                       movable=movable)

        # Lines can be moved to adjust location of channels along the probe track
        # Ensure distance between bottom and top channel is always constant at 3840um and that
        # lines can't be moved outside interpolation bounds
        # Add offset of 1um to keep within bounds of interpolation
        offset = 1
        self.tip_pos.setBounds((self.loaddata.track[self.idx][0] * 1e6 + offset,
                                self.loaddata.track[self.idx][-1] * 1e6 -
                                (self.probe_top + offset)))
        self.top_pos.setBounds((self.loaddata.track[self.idx][0] * 1e6 + (self.probe_top + offset),
                                self.loaddata.track[self.idx][-1] * 1e6 - offset))
        self.tip_pos.sigPositionChanged.connect(self.tip_line_moved)
        self.top_pos.sigPositionChanged.connect(self.top_line_moved)

        # Add lines to figure
        fig.addItem(self.tip_pos)
        fig.addItem(self.top_pos)

    def create_hist_data(self, reg, chan_int):
        """
        Creates a rectangular step function along y axis
        :param reg: y bounds
        :type reg: np.array([min_y_val, max_y_val])
        :param chan_int: steps
        :type chan_int: int
        """
        y = np.arange(reg[0], reg[1] + chan_int, chan_int, dtype=int)
        x = np.ones(len(y), dtype=int)
        x = np.r_[0, x, 0]
        y = np.r_[reg[0], y, reg[1]]
        return x, y

    def offset_hist_data(self):
        """
        Offset location of probe tip along probe track
        """
        self.loaddata.track[self.idx] = (self.loaddata.track[self.idx_prev] +
                                         self.tip_pos.value() / 1e6)
        self.loaddata.features[self.idx] = (self.loaddata.features[self.idx_prev])

        self.loaddata.scale_histology_regions(self.idx)
        self.loaddata.get_scale_factor(self.idx)

    def scale_hist_data(self):
        """
        Scale brain regions along probe track
        """
        # Track --> histology plot
        line_track = np.array([line[0].pos().y() for line in self.lines_tracks]) / 1e6
        # Feature --> ephys data plots
        line_feature = np.array([line[0].pos().y() for line in self.lines_features]) / 1e6
        depths_track = np.sort(np.r_[self.loaddata.track[self.idx_prev][[0, -1]], line_track])

        self.loaddata.track[self.idx] = self.loaddata.feature2track(depths_track, self.idx_prev)
        self.loaddata.features[self.idx] = np.sort(np.r_[self.loaddata.features[self.idx_prev]
                                                   [[0, -1]], line_feature])

        if ((self.loaddata.features[self.idx].size >= 5) & self.lin_fit):
            self.loaddata.features[self.idx][0] -= self.extend_feature
            self.loaddata.features[self.idx][-1] += self.extend_feature
            extend_track = self.loaddata.feature2track_lin(self.loaddata.features
                                                           [self.idx][[0, -1]], self.idx)
            self.loaddata.track[self.idx][0] = extend_track[0]
            self.loaddata.track[self.idx][-1] = extend_track[-1]

        else:
            diff = np.diff(self.loaddata.features[self.idx] - self.loaddata.track[self.idx])
            self.loaddata.track[self.idx][0] -= diff[0]
            self.loaddata.track[self.idx][-1] += diff[-1]

        self.loaddata.scale_histology_regions(self.idx)
        self.loaddata.get_scale_factor(self.idx)

    def plot_scale_factor(self):
        """
        Plots the scale factor applied to brain regions along probe track, displayed
        alongside histology figure
        """
        self.fig_scale.clear()
        self.scale_regions = np.empty((0, 1))
        self.scale_factor = self.loaddata.scale_data['scale'][self.idx]
        scale_factor = self.loaddata.scale_data['scale'][self.idx] - 0.5
        color_bar = cb.ColorBar('seismic')
        cbar = color_bar.makeColourBar(20, 5, self.fig_scale_cb, min=0.5, max=1.5,
                                       label='Scale Factor')
        colours = color_bar.map.mapToQColor(scale_factor)

        for ir, reg in enumerate(self.loaddata.scale_data['region'][self.idx]):
            region = pg.LinearRegionItem(values=(reg[0], reg[1]),
                                         orientation=pg.LinearRegionItem.Horizontal,
                                         brush=colours[ir], movable=False)
            region.setZValue(100)
            bound = pg.InfiniteLine(pos=reg[0], angle=0, pen=colours[ir])
            bound.setZValue(101)

            self.fig_scale.addItem(region)
            self.fig_scale.addItem(bound)
            self.scale_regions = np.vstack([self.scale_regions, region])

        bound = pg.InfiniteLine(pos=self.loaddata.scale_data['region'][self.idx][-1][1], angle=0,
                                pen=colours[-1])
        bound.setZValue(101)
        self.fig_scale.addItem(bound)

        self.fig_scale.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                 self.probe_extra, padding=self.pad)
        self.fig_scale_cb.addItem(cbar)

    def plot_fit(self):
        """
        Plots the scale factor and offset applied to channels along depth of probe track
        relative to orignal position of channels
        """
        self.fit_plot.setData(x=self.loaddata.features[self.idx] * 1e6,
                              y=self.loaddata.track[self.idx] * 1e6)
        self.fit_scatter.setData(x=self.loaddata.features[self.idx] * 1e6,
                                 y=self.loaddata.track[self.idx] * 1e6)

        depth_lin = self.loaddata.feature2track_lin(self.depth / 1e6, self.idx)
        if np.any(depth_lin):
            self.fit_plot_lin.setData(x=self.depth, y=depth_lin * 1e6)
        else:
            self.fit_plot_lin.setData()

    def plot_slice_orig(self):
        """
        Plots a tilted coronal slice of the Allen brain atlas annotation volume with probe
        track and channel positions overlaid
        """
        self.fig_slice_ax.cla()
        xyz_trk = self.loaddata.xyz_track
        # recomputes from scratch, for hovering function it would have to be pre-computed
        xyz_ch = self.loaddata.get_channels_coordinates(self.idx)
        self.loaddata.brain_atlas.plot_tilted_slice(xyz_trk, axis=1, volume='annotation',
                                                    ax=self.fig_slice_ax)
        self.fig_slice_ax.plot(xyz_trk[:, 0] * 1e6, xyz_trk[:, 2] * 1e6, 'b')
        self.fig_slice_ax.plot(xyz_ch[:, 0] * 1e6, xyz_ch[:, 2] * 1e6, 'k*', markersize=6)
        self.fig_slice_ax.axis('off')
        self.fig_slice.draw()


    def plot_slice(self, data, img_type):
        self.fig_slice.clear()
        self.slice_chns = []
        img = pg.ImageItem()
        #self.slice_img.clear()
        img.setImage(data[img_type])
        if img_type == 'label':
            img.translate(data['offset'][0], data['offset'][1])
            img.scale(data['scale'][0], data['scale'][1])
        else:
            img.translate(data['offset'][0], data['offset'][1])
            img.scale(data['scale'][0], data['scale'][1])
            color_bar = cb.ColorBar('cividis')
            lut = color_bar.getColourMap()
            img.setLookupTable(lut)

        self.fig_slice.addItem(img)
        traj = pg.PlotCurveItem()
        traj.setData(x=self.loaddata.xyz_track[:, 0], y=self.loaddata.xyz_track[:, 2], pen='g')
        self.fig_slice.addItem(traj)

        self.plot_channels()


    def plot_channels(self):
        xyz_ch = self.loaddata.get_channels_coordinates(self.idx)
        if not self.slice_chns:
            self.slice_chns = pg.ScatterPlotItem()
            self.slice_chns.setData(x=xyz_ch[:, 0], y=xyz_ch[:, 2], pen='r', brush='r')
            self.fig_slice.addItem(self.slice_chns)
        else:
            self.slice_chns.setData(x=xyz_ch[:, 0], y=xyz_ch[:, 2], pen='r', brush='r')


    def plot_scatter(self, data):
        """
        Plots a 2D scatter plot with electrophysiology data
        param data: dictionary of data to plot
            {'x': x coordinate of data, np.array((npoints)), float
             'y': y coordinate of data, np.array((npoints)), float
             'size': size of data, np.array((npoints)), float
             'colour': colour of data, np.array((npoints)), QtGui.QColor
             'xrange': range to display of x axis, np.array([min range, max range]), float
             'xaxis': label for xaxis, string
            }
        type data: dict
        """
        if not data:
            print('data for this plot not available')
            return
        else:
            [self.fig_img.removeItem(plot) for plot in self.img_plots]
            [self.fig_img_cb.removeItem(cbar) for cbar in self.img_cbars]
            self.img_plots = []
            self.img_cbars = []
            connect = np.zeros(data['x'].size, dtype=int)
            size = data['size'].tolist()
            symbol = data['symbol'].tolist()

            color_bar = cb.ColorBar(data['cmap'])
            cbar = color_bar.makeColourBar(20, 5, self.fig_img_cb, min=np.min(data['levels'][0]),
                                           max=np.max(data['levels'][1]), label=data['title'])
            self.fig_img_cb.addItem(cbar)
            self.img_cbars.append(cbar)

            if type(np.any(data['colours'])) == QtGui.QColor:
                brush = data['colours'].tolist()
            else:
                brush = color_bar.map.mapToQColor(data['colours'])

            plot = pg.PlotDataItem()
            plot.setData(x=data['x'], y=data['y'], connect=connect,
                         symbol=symbol, symbolSize=size, symbolBrush=brush, symbolPen=data['pen'])
            self.fig_img.addItem(plot)
            self.fig_img.setXRange(min=data['xrange'][0], max=data['xrange'][1],
                                   padding=0)
            self.fig_img.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                   self.probe_extra, padding=self.pad)
            self.set_axis(self.fig_img, 'bottom', label=data['xaxis'])
            self.scale = 1
            self.img_plots.append(plot)
            self.data_plot = plot
            self.xrange = data['xrange']

            if data['cluster']:
                self.data = data['x']
                self.data_plot.sigPointsClicked.connect(self.cluster_clicked)
         
    def plot_line(self, data):
        """
        Plots a 1D line plot with electrophysiology data
        param data: dictionary of data to plot
            {'x': x coordinate of data, np.array((npoints)), float
             'y': y coordinate of data, np.array((npoints)), float
             'xrange': range to display of x axis, np.array([min range, max range]), float
             'xaxis': label for xaxis, string
            }
        type data: dict
        """
        if not data:
            print('data for this plot not available')
            return
        else:
            [self.fig_line.removeItem(plot) for plot in self.line_plots]
            self.line_plots = []
            line = pg.PlotCurveItem()
            line.setData(x=data['x'], y=data['y'])
            line.setPen('k')
            self.fig_line.addItem(line)
            self.fig_line.setXRange(min=data['xrange'][0], max=data['xrange'][1], padding=0)
            self.fig_line.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                    self.probe_extra, padding=self.pad)
            self.set_axis(self.fig_line, 'bottom', label=data['xaxis'])
            self.line_plots.append(line)

    def plot_probe(self, data):
        """
        Plots a 2D image with probe geometry
        param data: dictionary of data to plot
            {'img': image data for each channel bank, list of np.array((1,ny)), list
             'scale': scaling to apply to each image, list of np.array([xscale,yscale]), list
             'offset': offset to apply to each image, list of np.array([xoffset,yoffset]), list
             'level': colourbar extremes np.array([min val, max val]), float
             'cmap': colourmap to use, string
             'xrange': range to display of x axis, np.array([min range, max range]), float
             'title': description to place on colorbar, string
            }
        type data: dict
        """
        if not data:
            print('data for this plot not available')
            return
        else:
            [self.fig_probe.removeItem(plot) for plot in self.probe_plots]
            [self.fig_probe_cb.removeItem(cbar) for cbar in self.probe_cbars]
            self.set_axis(self.fig_probe_cb, 'top', pen='w')
            self.probe_plots = []
            self.probe_cbars = []
            color_bar = cb.ColorBar(data['cmap'])
            lut = color_bar.getColourMap()
            for img, scale, offset in zip(data['img'], data['scale'], data['offset']):
                image = pg.ImageItem()
                image.setImage(img)
                image.translate(offset[0], offset[1])
                image.scale(scale[0], scale[1])
                image.setLookupTable(lut)
                image.setLevels((data['level'][0], data['level'][1]))
                self.fig_probe.addItem(image)
                self.probe_plots.append(image)

            cbar = color_bar.makeColourBar(20, 5, self.fig_probe_cb, min=data['level'][0],
                                           max=data['level'][1], label=data['title'], lim=True)
            self.fig_probe_cb.addItem(cbar)
            self.probe_cbars.append(cbar)

            self.fig_probe.setXRange(min=data['xrange'][0], max=data['xrange'][1], padding=0)
            self.fig_probe.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                     self.probe_extra, padding=self.pad)

    def plot_image(self, data):
        """
        Plots a 2D image with with electrophysiology data
        param data: dictionary of data to plot
            {'img': image data, np.array((nx,ny)), float
             'scale': scaling to apply to each axis, np.array([xscale,yscale]), float
             'level': colourbar extremes np.array([min val, max val]), float
             'cmap': colourmap to use, string
             'xrange': range to display of x axis, np.array([min range, max range]), float
             'xaxis': label for xaxis, string
             'title': description to place on colorbar, string
            }
        type data: dict
        """
        if not data:
            print('data for this plot not available')
            return
        else:
            [self.fig_img.removeItem(plot) for plot in self.img_plots]
            [self.fig_img_cb.removeItem(cbar) for cbar in self.img_cbars]
            self.set_axis(self.fig_img_cb, 'top', pen='w')
            self.img_plots = []
            self.img_cbars = []

            image = pg.ImageItem()
            image.setImage(data['img'])
            image.scale(data['scale'][0], data['scale'][1])
            cmap = data.get('cmap', [])
            if cmap:
                color_bar = cb.ColorBar(data['cmap'])
                lut = color_bar.getColourMap()
                image.setLookupTable(lut)
                image.setLevels((data['levels'][0], data['levels'][1]))
                cbar = color_bar.makeColourBar(20, 5, self.fig_img_cb, min=data['levels'][0],
                                               max=data['levels'][1], label=data['title'])
                self.fig_img_cb.addItem(cbar)
                self.img_cbars.append(cbar)
            else:
                image.setLevels((1, 0))

            self.fig_img.addItem(image)
            self.img_plots.append(image)
            self.fig_img.setXRange(min=data['xrange'][0], max=data['xrange'][1], padding=0)
            self.fig_img.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                   self.probe_extra, padding=self.pad)
            self.set_axis(self.fig_img, 'bottom', label=data['xaxis'])
            self.scale = data['scale'][1]
            self.data_plot = image
            self.xrange = data['xrange']

    """
    Interaction functions
    """
    def on_subject_selected(self, idx):
        """
        Triggered when subject is selected from drop down list options
        :param idx: index chosen subject (item) in drop down list
        :type idx: int
        """
        self.sess_list.clear()
        sessions = self.loaddata.get_sessions(idx)
        self.populate_lists(sessions, self.sess_list, self.sess_combobox)
        self.loaddata.get_info(0)

    def on_session_selected(self, idx):
        """
        Triggered when session is selected from drop down list options
        :param idx: index of chosen session (item) in drop down list
        :type idx: int
        """
        self.loaddata.get_info(idx)

    def data_button_pressed(self):
        """
        Triggered when Get Data button pressed, uses subject and session info to find eid and
        downloads and computes data needed for GUI display
        """
        # Clear all plots from previous session
        [self.fig_img.removeItem(plot) for plot in self.img_plots]
        [self.fig_img.removeItem(cbar) for cbar in self.img_cbars]
        [self.fig_line.removeItem(plot) for plot in self.line_plots]
        [self.fig_probe.removeItem(plot) for plot in self.probe_plots]
        [self.fig_probe.removeItem(cbar) for cbar in self.probe_cbars]
        self.fit_plot.setData()
        self.remove_lines_points()
        self.init_variables()

        self.loaddata.get_eid()
        alf_path, ephys_path, self.sess_notes = self.loaddata.get_data()
        self.loaddata.get_probe_track()
        self.plotdata = pd.PlotData(alf_path, ephys_path)
        self.slice_data = self.loaddata.get_slice_images()

        self.scat_drift_data = self.plotdata.get_depth_data_scatter()
        (self.scat_fr_data, self.scat_p2t_data,
         self.scat_amp_data) = self.plotdata.get_fr_p2t_data_scatter()
        self.img_corr_data = self.plotdata.get_correlation_data_img()
        self.img_fr_data = self.plotdata.get_fr_img()
        self.img_rms_APdata, self.probe_rms_APdata = self.plotdata.get_rms_data_img_probe('AP')
        self.img_rms_LFPdata, self.probe_rms_LFPdata = self.plotdata.get_rms_data_img_probe('LF')
        self.img_lfp_data, self.probe_lfp_data = self.plotdata.get_lfp_spectrum_data()
        self.line_fr_data, self.line_amp_data = self.plotdata.get_fr_amp_data_line()

        # Initialise checked plots
        self.img_init.setChecked(True)
        self.line_init.setChecked(True)
        self.probe_init.setChecked(True)
        self.unit_init.setChecked(True)
        self.slice_init.setChecked(True)

        # Initialise ephys plots
        self.plot_image(self.img_fr_data)
        self.plot_probe(self.probe_rms_APdata)
        self.plot_line(self.line_fr_data)

        # Initialise histology plots
        self.plot_histology(self.fig_hist_ref, ax='right', movable=False)
        self.plot_histology(self.fig_hist)
        self.plot_scale_factor()

        # Initialise slice and fit images
        self.plot_fit()
        self.plot_slice(self.slice_data, 'hist')

        # Only configure the view the first time the GUI is launched
        self.set_view(view=1, configure=self.configure)
        self.configure = False

    def filter_unit_pressed(self, type):
        self.plotdata.filter_units(type)
        self.scat_drift_data = self.plotdata.get_depth_data_scatter()
        (self.scat_fr_data, self.scat_p2t_data,
         self.scat_amp_data) = self.plotdata.get_fr_p2t_data_scatter()
        self.img_corr_data = self.plotdata.get_correlation_data_img()
        self.img_fr_data = self.plotdata.get_fr_img()
        self.line_fr_data, self.line_amp_data = self.plotdata.get_fr_amp_data_line()
        self.img_init.setChecked(True)
        self.line_init.setChecked(True)
        self.probe_init.setChecked(True)
        self.plot_image(self.img_fr_data)
        self.plot_probe(self.probe_rms_APdata)
        self.plot_line(self.line_fr_data)

    def fit_button_pressed(self):
        """
        Triggered when fit button or Enter key pressed, applies scaling factor to brain regions
        according to locations of reference lines on ephys and histology plots. Updates all plots
        and indices after scaling has been applied
        """
        # Use a cyclic buffer of length self.max_idx to hold information about previous moves,
        # when a new move is initiated ensures indexes are all correct so user can only access
        # fixed number of previous or next moves
        if self.current_idx < self.last_idx:
            self.total_idx = np.copy(self.current_idx)
            self.diff_idx = (np.mod(self.last_idx, self.max_idx) - np.mod(self.total_idx,
                                                                          self.max_idx))
            if self.diff_idx >= 0:
                self.diff_idx = self.max_idx - self.diff_idx
            else:
                self.diff_idx = np.abs(self.diff_idx)
        else:
            self.diff_idx = self.max_idx - 1

        self.total_idx += 1
        self.current_idx += 1
        self.idx_prev = np.copy(self.idx)
        self.idx = np.mod(self.current_idx, self.max_idx)
        self.scale_hist_data()
        self.plot_histology(self.fig_hist)
        self.plot_scale_factor()
        self.plot_fit()
        self.plot_channels()
        self.remove_lines_points()
        self.add_lines_points()
        self.update_lines_points()
        self.fig_hist.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                self.probe_extra, padding=self.pad)
        self.update_string()

    def offset_button_pressed(self):
        """
        Triggered when offset button or o key pressed, applies offset to brain regions according to
        locations of probe tip line on histology plot. Updates all plots and indices after offset
        has been applied
        """

        if self.current_idx < self.last_idx:
            self.total_idx = np.copy(self.current_idx)
            self.diff_idx = (np.mod(self.last_idx, self.max_idx) - np.mod(self.total_idx,
                                                                          self.max_idx))
            if self.diff_idx >= 0:
                self.diff_idx = self.max_idx - self.diff_idx
            else:
                self.diff_idx = np.abs(self.diff_idx)
        else:
            self.diff_idx = self.max_idx - 1

        self.total_idx += 1
        self.current_idx += 1
        self.idx_prev = np.copy(self.idx)
        self.idx = np.mod(self.current_idx, self.max_idx)
        self.offset_hist_data()
        self.plot_histology(self.fig_hist)
        self.plot_scale_factor()
        self.plot_fit()
        self.plot_channels()
        self.remove_lines_points()
        self.add_lines_points()
        self.update_lines_points()
        self.fig_hist.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                self.probe_extra, padding=self.pad)
        self.update_string()

    def movedown_button_pressed(self):
        """
        Triggered when Shift+down key pressed. Moves probe tip down by 50um and offsets data
        """
        if self.loaddata.track[self.idx][-1] - 50 / 1e6 >= np.max(self.loaddata.chn_coords
                                                                  [:, 1]) / 1e6:
            self.loaddata.track[self.idx] -= 50 / 1e6
            self.offset_button_pressed()

    def moveup_button_pressed(self):
        """
        Triggered when Shift+down key pressed. Moves probe tip up by 50um and offsets data
        """
        if self.loaddata.track[self.idx][0] + 50 / 1e6 <= np.min(self.loaddata.chn_coords
                                                                 [:, 1]) / 1e6:
            self.loaddata.track[self.idx] += 50 / 1e6
            self.offset_button_pressed()

    def toggle_labels_button_pressed(self):
        """
        Triggered when Shift+A key pressed. Shows/hides labels Allen atlas labels on brain regions
        in histology plots
        """
        self.label_status = not self.label_status
        if not self.label_status:
            self.ax_hist_ref.setPen(None)
            self.ax_hist.setPen(None)
            self.fig_hist_ref.update()
            self.fig_hist.update()

        else:
            self.ax_hist_ref.setPen('k')
            self.ax_hist.setPen('k')
            self.fig_hist_ref.update()
            self.fig_hist.update()

    def toggle_line_button_pressed(self):
        """
        Triggered when Shift+L key pressed. Shows/hides reference lines on ephys and histology
        plots
        """
        self.line_status = not self.line_status
        if not self.line_status:
            self.remove_lines_points()
        else:
            self.add_lines_points()

    def delete_line_button_pressed(self):
        """
        Triggered when mouse hovers over reference line and Del key pressed. Deletes a reference
        line from the ephys and histology plots
        """

        if self.selected_line:
            line_idx = np.where(self.lines_features == self.selected_line)[0]
            if line_idx.size == 0:
                line_idx = np.where(self.lines_tracks == self.selected_line)[0]
            line_idx = line_idx[0]

            self.fig_img.removeItem(self.lines_features[line_idx][0])
            self.fig_line.removeItem(self.lines_features[line_idx][1])
            self.fig_probe.removeItem(self.lines_features[line_idx][2])
            self.fig_hist.removeItem(self.lines_tracks[line_idx, 0])
            self.fig_fit.removeItem(self.points[line_idx, 0])
            self.lines_features = np.delete(self.lines_features, line_idx, axis=0)
            self.lines_tracks = np.delete(self.lines_tracks, line_idx, axis=0)
            self.points = np.delete(self.points, line_idx, axis=0)

    def next_button_pressed(self):
        """
        Triggered when right key pressed. Updates all plots and indices with next move. Ensures
        user cannot go past latest move
        """
        if (self.current_idx < self.total_idx) & (self.current_idx >
                                                  self.total_idx - self.max_idx):
            self.current_idx += 1
            self.idx = np.mod(self.current_idx, self.max_idx)
            self.remove_lines_points()
            self.add_lines_points()
            self.plot_histology(self.fig_hist)
            self.plot_scale_factor()
            self.remove_lines_points()
            self.add_lines_points()
            self.plot_fit()
            self.plot_channels()
            self.update_string()

    def prev_button_pressed(self):
        """
        Triggered when left key pressed. Updates all plots and indices with previous move.
        Ensures user cannot go back more than self.max_idx moves
        """
        if self.total_idx > self.last_idx:
            self.last_idx = np.copy(self.total_idx)

        if (self.current_idx > np.max([0, self.total_idx - self.diff_idx])):
            self.current_idx -= 1
            self.idx = np.mod(self.current_idx, self.max_idx)
            self.remove_lines_points()
            self.add_lines_points()
            self.plot_histology(self.fig_hist)
            self.plot_scale_factor()
            self.remove_lines_points()
            self.add_lines_points()
            self.plot_fit()
            self.plot_channels()
            self.update_string()

    def reset_button_pressed(self):
        """
        Triggered when reset button or Shift+R key pressed. Resets channel locations to orignal
        location
        """
        self.remove_lines_points()
        self.lines_features = np.empty((0, 3))
        self.lines_tracks = np.empty((0, 1))
        self.points = np.empty((0, 1))
        if self.current_idx < self.last_idx:
            self.total_idx = np.copy(self.current_idx)
            self.diff_idx = (np.mod(self.last_idx, self.max_idx) - np.mod(self.total_idx,
                                                                          self.max_idx))
            if self.diff_idx >= 0:
                self.diff_idx = self.max_idx - self.diff_idx
            else:
                self.diff_idx = np.abs(self.diff_idx)
        else:
            self.diff_idx = self.max_idx - 1

        self.total_idx += 1
        self.current_idx += 1
        self.idx = np.mod(self.current_idx, self.max_idx)
        self.loaddata.track[self.idx] = np.copy(self.loaddata.track_init)
        self.loaddata.features[self.idx] = np.copy(self.loaddata.track_init)
        self.loaddata.scale_histology_regions(self.idx)
        self.loaddata.get_scale_factor(self.idx)
        self.plot_histology(self.fig_hist)
        self.plot_scale_factor()
        self.plot_fit()
        self.plot_channels()
        self.fig_hist.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                self.probe_extra, padding=self.pad)
        self.update_string()

    def complete_button_pressed(self):
        """
        Triggered when complete button or Shift+F key pressed. Uploads final channel locations to
        Alyx
        """
        upload = QtGui.QMessageBox.question(self, '',
                                            "Upload final channel locations to Alyx?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if upload == QtGui.QMessageBox.Yes:
            if self.loaddata.traj_exists:

                overwrite = QtGui.QMessageBox.warning(self, '', ("Ephys aligned trajectory "
                                                      "for this probe insertion already exists on "
                                                      "Alyx. Do you want to overwrite?"),
                                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                if overwrite == QtGui.QMessageBox.Yes:
                    self.loaddata.upload_channels(overwrite=True)
                    self.loaddata.get_trajectory()
                    QtGui.QMessageBox.information(self, '', ("Electrode locations "
                                                  "succesfully uploaded to Alyx"))
                else:
                    pass
                    QtGui.QMessageBox.information(self, '', ("Electrode locations not "
                                                  "uploaded to Alyx"))
            else:
                self.loaddata.upload_channels()
                self.loaddata.get_trajectory()
                QtGui.QMessageBox.information(self, 'Status', ("Electrode locations "
                                              "succesfully uploaded to Alyx"))
        else:
            pass
            QtGui.QMessageBox.information(self, 'Status', ("Electrode locations not uploaded"
                                          " to Alyx"))

    def reset_axis_button_pressed(self):
        self.fig_hist.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                self.probe_extra, padding=self.pad)
        self.fig_hist_ref.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                                    self.probe_extra, padding=self.pad)
        self.fig_img.setXRange(min=self.xrange[0], max=self.xrange[1], padding=0)
        self.fig_img.setYRange(min=self.probe_tip - self.probe_extra, max=self.probe_top +
                               self.probe_extra, padding=self.pad)

    def display_session_notes(self):
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle('Session notes from Alyx')
        dialog.resize(200, 100)
        notes = QtGui.QTextEdit()
        notes.setReadOnly(True)
        notes.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        notes.setText(self.sess_notes)
        dialog_layout = QtGui.QVBoxLayout()
        dialog_layout.addWidget(notes)
        dialog.setLayout(dialog_layout)
        dialog.show()

    def popup_closed(self, popup):
        popup_idx = [iP for iP, pop in enumerate(self.cluster_popups) if pop == popup][0]
        self.cluster_popups.pop(popup_idx)

    def popup_moved(self):
        self.activateWindow()

    def close_popups(self):
        for pop in self.cluster_popups:
            pop.blockSignals(True)
            pop.close()
        self.cluster_popups = []

    def minimise_popups(self):
        self.popup_status = not self.popup_status
        if self.popup_status:
            for pop in self.cluster_popups:
                pop.showNormal()
            self.activateWindow()
        else:
            for pop in self.cluster_popups:
                pop.showMinimized()
            self.activateWindow()

    def lin_fit_option_changed(self, state):
        if state == 0:
            self.lin_fit = False
            self.fit_button_pressed()
        else:
            self.lin_fit = True
            self.fit_button_pressed()

    def cluster_clicked(self, item, point):
        point_pos = point[0].pos()
        clust_idx = np.argwhere(self.data == point_pos.x())[0][0]

        autocorr = self.plotdata.get_autocorr(clust_idx)
        autocorr_plot = pg.PlotItem()
        autocorr_plot.setXRange(min=np.min(self.plotdata.t_autocorr),
                                max=np.max(self.plotdata.t_autocorr))
        autocorr_plot.setYRange(min=0, max=1.05 * np.max(autocorr))
        self.set_axis(autocorr_plot, 'bottom', label='T (ms)')
        self.set_axis(autocorr_plot, 'left', label='Number of spikes')
        plot = pg.BarGraphItem()
        plot.setOpts(x=self.plotdata.t_autocorr, height=autocorr, width=0.24,
                     brush=self.bar_colour)
        autocorr_plot.addItem(plot)

        template_wf = self.plotdata.get_template_wf(clust_idx)
        template_plot = pg.PlotItem()
        plot = pg.PlotCurveItem()
        template_plot.setXRange(min=np.min(self.plotdata.t_template),
                                max=np.max(self.plotdata.t_template))
        self.set_axis(template_plot, 'bottom', label='T (ms)')
        self.set_axis(template_plot, 'left', label='Amplitude (a.u.)')
        plot.setData(x=self.plotdata.t_template, y=template_wf, pen=self.kpen_solid)
        template_plot.addItem(plot)

        clust_layout = pg.GraphicsLayout()
        clust_layout.addItem(autocorr_plot, 0, 0)
        clust_layout.addItem(template_plot, 1, 0)

        self.clust_win = ephys_gui.ClustPopupWindow(title=f'Cluster {clust_idx}')
        self.clust_win.closed.connect(self.popup_closed)
        self.clust_win.moved.connect(self.popup_moved)
        self.clust_win.clust_widget.addItem(autocorr_plot, 0, 0)
        self.clust_win.clust_widget.addItem(template_plot, 1, 0)
        self.cluster_popups.append(self.clust_win)
        self.activateWindow()

    def on_mouse_double_clicked(self, event):
        """
        Triggered when a double click event is detected on ephys of histology plots. Adds reference
        line on ephys and histology plot that can be moved to align ephys signatures with brain
        regions. Also adds scatter point on fit plot
        :param event: double click event signal
        :type event: pyqtgraph mouseEvents
        """
        if event.double():
            pos = self.data_plot.mapFromScene(event.scenePos())
            pen, brush = self.create_line_style()
            line_track = pg.InfiniteLine(pos=pos.y() * self.scale, angle=0, pen=pen, movable=True)
            line_track.sigPositionChanged.connect(self.update_lines_track)
            line_track.setZValue(100)
            line_feature1 = pg.InfiniteLine(pos=pos.y() * self.scale, angle=0, pen=pen,
                                            movable=True)
            line_feature1.setZValue(100)
            line_feature1.sigPositionChanged.connect(self.update_lines_features)
            line_feature2 = pg.InfiniteLine(pos=pos.y() * self.scale, angle=0, pen=pen,
                                            movable=True)
            line_feature2.setZValue(100)
            line_feature2.sigPositionChanged.connect(self.update_lines_features)
            line_feature3 = pg.InfiniteLine(pos=pos.y() * self.scale, angle=0, pen=pen,
                                            movable=True)
            line_feature3.setZValue(100)
            line_feature3.sigPositionChanged.connect(self.update_lines_features)
            self.fig_hist.addItem(line_track)
            self.fig_img.addItem(line_feature1)
            self.fig_line.addItem(line_feature2)
            self.fig_probe.addItem(line_feature3)

            self.lines_features = np.vstack([self.lines_features, [line_feature1, line_feature2,
                                                                   line_feature3]])
            self.lines_tracks = np.vstack([self.lines_tracks, line_track])

            point = pg.PlotDataItem()
            point.setData(x=[line_track.pos().y()], y=[line_feature1.pos().y()],
                          symbolBrush=brush, symbol='o', symbolSize=10)
            self.fig_fit.addItem(point)
            self.points = np.vstack([self.points, point])

    def on_mouse_hover(self, items):
        """
        Returns the pyqtgraph items that the mouse is hovering over. Used to identify reference
        lines so that they can be deleted
        """
        if items:
            self.selected_line = []
            if type(items[0]) == pg.InfiniteLine:
                self.selected_line = items[0]
            elif type(items[0]) == pg.LinearRegionItem:
                idx = np.where(self.scale_regions == items[0])[0][0]
                self.fig_scale_ax.setLabel('Scale Factor = ' +
                                           str(np.around(self.scale_factor[idx], 2)))

    def update_lines_features(self, line):
        """
        Triggered when reference line on ephys data plots is moved. Moves all three lines on the
        img_plot, line_plot and probe_plot and adjusts the corresponding point on the fit plot
        :param line: selected line
        :type line: pyqtgraph InfiniteLine
        """
        idx = np.where(self.lines_features == line)
        line_idx = idx[0][0]
        fig_idx = np.setdiff1d(np.arange(0, 3), idx[1][0])

        self.lines_features[line_idx][fig_idx[0]].setPos(line.value())
        self.lines_features[line_idx][fig_idx[1]].setPos(line.value())

        self.points[line_idx][0].setData(x=[self.lines_features[line_idx][0].pos().y()],
                                         y=[self.lines_tracks[line_idx][0].pos().y()])

    def update_lines_track(self, line):
        """
        Triggered when reference line on histology plot is moved. Adjusts the corresponding point
        on the fit plot
        :param line: selected line
        :type line: pyqtgraph InfiniteLine
        """
        line_idx = np.where(self.lines_tracks == line)[0][0]

        self.points[line_idx][0].setData(x=[self.lines_features[line_idx][0].pos().y()],
                                         y=[self.lines_tracks[line_idx][0].pos().y()])

    def tip_line_moved(self):
        """
        Triggered when dotted line indicating probe tip on self.fig_hist moved. Gets the y pos of
        probe tip line and ensures the probe top line is set to probe tip line y pos + 3840
        """
        self.top_pos.setPos(self.tip_pos.value() + self.probe_top)

    def top_line_moved(self):
        """
        Triggered when dotted line indicating probe top on self.fig_hist moved. Gets the y pos of
        probe top line and ensures the probe tip line is set to probe top line y pos - 3840
        """
        self.tip_pos.setPos(self.top_pos.value() - self.probe_top)

    def remove_lines_points(self):
        """
        Removes all reference lines and scatter points from the ephys, histology and fit plots
        """
        for line_feature, line_track, point in zip(self.lines_features, self.lines_tracks,
                                                   self.points):
            self.fig_img.removeItem(line_feature[0])
            self.fig_line.removeItem(line_feature[1])
            self.fig_probe.removeItem(line_feature[2])
            self.fig_hist.removeItem(line_track[0])
            self.fig_fit.removeItem(point[0])

    def add_lines_points(self):
        """
        Adds all reference lines and scatter points from the ephys, histology and fit plots
        """
        for line_feature, line_track, point in zip(self.lines_features, self.lines_tracks,
                                                   self.points):
            self.fig_img.addItem(line_feature[0])
            self.fig_line.addItem(line_feature[1])
            self.fig_probe.addItem(line_feature[2])
            self.fig_hist.addItem(line_track[0])
            self.fig_fit.addItem(point[0])

    def update_lines_points(self):
        """
        Updates position of reference lines on histology plot after fit has been applied. Also
        updates location of scatter point
        """
        for line_feature, line_track, point in zip(self.lines_features, self.lines_tracks,
                                                   self.points):
            line_track[0].setPos(line_feature[0].getYPos())
            point[0].setData(x=[line_feature[0].pos().y()], y=[line_feature[0].pos().y()])

    def create_line_style(self):
        """
        Create random choice of colour and style for reference line
        :return pen: style to use for the line
        :type pen: pyqtgraph Pen
        :return brush: colour use for the line
        :type brush: pyqtgraph Brush
        """
        colours = ['#000000', '#cc0000', '#6aa84f', '#1155cc', '#a64d79']
        style = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine, QtCore.Qt.DashDotLine]
        col = QtGui.QColor(colours[randrange(len(colours))])
        sty = style[randrange(len(style))]
        pen = pg.mkPen(color=col, style=sty, width=3)
        brush = pg.mkBrush(color=col)
        return pen, brush

    def update_string(self):
        """
        Updates text boxes to indicate to user which move they are looking at
        """
        self.idx_string.setText(f"Current Index = {self.current_idx}")
        self.tot_idx_string.setText(f"Total Index = {self.total_idx}")


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    mainapp = MainWindow()
    mainapp.show()
    app.exec_()