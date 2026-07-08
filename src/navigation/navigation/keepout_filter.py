import rclpy
import yaml
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from rclpy.node import Node
from math import ceil
from ament_index_python.packages import get_package_share_directory

origin_x = 0                        
origin_y = 0


class KeepoutFilter(Node):
    def __init__(self):
        '''
        Given :
        The rack structure and the arrangement (and dimensions of each rack), an occupancy grid from SLAM of the arena for the initial 2 minutes.
        There is a safety zone 10 cm from the rack to 25cm from the rack or if no rack in that side, then from wall, avoid obstacles in the way 
        the safety zone curves around the obstacles, obstacles are cylinders of 20cm diameter one set of wheels facing the rack or the wall have to always be in the safety zone

        What's being done in this code:
        1. Using slam toolbox for the initial mapping and teleop control to move the bot
        2. For the navigation , Nav2 will be  with a keepout filter we designed so that the wheels of the bot dont cross the safety zone
        3. The keepout filter for Nav2 perform image processing on that map and generate the keepout filter.
        4. We extract rack positions and thus optimal scanning positions for each rack, and assign two optimal positions for each rack for better scanning range of QR codes
        5. We then define all the 10 optimal scanning positions (5 racks) and other intermediate postions as the way points to Nav2.

        '''

        super().__init__("keepout_filter")

        #package_share = get_package_share_directory('navigation')
        #arena_file = os.path.join(package_share, 'config', 'arena.yaml')

        arena_file = os.path.expanduser("~/arena.yaml")
 
        #read data from the yaml file saved from the teleop-slam 
        with open(arena_file, "r") as file:
            data = yaml.safe_load(file)

        #store data from yaml
        origin_x = data["origin"][0]
        origin_y = data["origin"][1]
        resolution = data["resolution"]

        #inverse perspective transform for the optimal rack scanning points
        def get_transformed_optimal_pos(optimal_pos, Minv):
            #enumerate through all points 
            for i, pos in enumerate(optimal_pos):
                extend_pos = np.array([pos[0], pos[1], 1]).reshape(-1, 1)
                #apply inverse perspective transform
                transf_pos = Minv @ extend_pos
                m = transf_pos[2]
                optimal_pos[i] = np.array([(transf_pos[0] / m), (transf_pos[1] / m)]).flatten()
            return optimal_pos

        # to give the detected corners from detector in clockwise sense
        def order_points(pts):
            pts = np.array(pts, dtype="float32")

            rect = np.zeros((4,2), dtype="float32")

            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]   
            rect[2] = pts[np.argmax(s)]   

            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]  
            rect[3] = pts[np.argmax(diff)] 

            return rect.astype(int)

        # for unique optimal positions
        optimal_pos = np.zeros((14, 2), dtype = "float32")

        img = cv2.imread(os.path.expanduser('~/arena.pgm'))

        plt.figure(figsize=(15, 10))
        plt.subplot(1, 2, 1)
        plt.imshow(img)

        ori_image = img

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


        inv = cv2.bitwise_not(img_gray)

        # dilate white (which were black before)
        kernel = np.ones((3,3), np.uint8)
        dilated = cv2.dilate(inv, kernel, iterations=1)

        # invert back 
        img_gray = cv2.bitwise_not(dilated)


        c , _ = cv2.findContours(img_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cv2.drawContours(img_gray, c, -1, 205, 3)

        #shi-tomasi corner detector, gives corners of the scanned map
        corners = cv2.goodFeaturesToTrack(
            img_gray,
            maxCorners=50,
            qualityLevel=0.01,
            minDistance=10,
            useHarrisDetector=True
        )

        corners = np.intp(corners)

        #bounding box of the detected corners
        rect = cv2.minAreaRect(np.array(corners))
        box = cv2.boxPoints(rect)
        box = np.intp(box)

        box = order_points(box)

        #width of the main arena
        widthA = np.linalg.norm(box[2] - box[3])
        widthB = np.linalg.norm(box[1] - box[0])
        maxWidth = int(max(widthA, widthB))

        #height of the main arena
        heightA = np.linalg.norm(box[1] - box[2])
        heightB = np.linalg.norm(box[0] - box[3])
        maxHeight = int(max(heightA, heightB))

        #slicing the main warehouse, excluding the aisle
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")


        #perspective transform of dst, and warping
        M = cv2.getPerspectiveTransform(box.astype("float32"), dst)
        img = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

        #plt.show()


        # use for inverted images only
        img = cv2.rotate(img, cv2.ROTATE_180)


        #plt.imshow(img)
        #plt.show()

        # dimensions of the arena
        length_w = 42
        width_w = 31

        # to compute the extra offset required to be added to the path
        warehouse_length = ceil(length_w / width_w * (len(img[0])))
        warehouse_length_in_pixels = warehouse_length / length_w
        warehouse_width_in_pixels = (1 / width_w) * len(img[0])
        w = ceil(40 * (warehouse_length_in_pixels / 100))

        # no.of layers of additional pixels to be added to 
        w = 10


        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inv = cv2.bitwise_not(img_gray)

        # dilate white (which were black before) !!! USE (3,3) FOR more resolution AND (1,1) FOR lower resolution 
        kernel = np.ones((1,1), np.uint8)
        dilated = cv2.dilate(inv, kernel, iterations=1)

        # invert back
        img_gray = cv2.bitwise_not(dilated)

        _, img_gray = cv2.threshold(img_gray, 200, 254, cv2.THRESH_BINARY)


        img_gray[ceil(warehouse_length - (warehouse_length_in_pixels)) : len(img), ceil((9 / 31) * len(img[0])) : len(img[0])] = 0

        #plt.imshow(img_gray, cmap="gray")
        #plt.show()

        #computing contours in the warped frame
        contours, _ = cv2.findContours(img_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = list(contours)
        length = len(contours)
        i = 0
        #eliminating the point contours and contours with area larger than 100
        while i < length:
            if cv2.contourArea(contours[i]) > 100 or cv2.contourArea(contours[i]) == 0:
                contours.pop(i)
                length -= 1
                i -= 1
            i += 1


        cv2.drawContours(img_gray, contours, -1, 120, 1)

        #plt.imshow(img_gray, cmap="gray")
        #plt.show()


        img_gray[0 : len(img), 0 : ceil(warehouse_length_in_pixels)] = 0


        points = np.zeros((len(contours), 2))

        i = 0


        #compute mean of the each rack pole contours to get the location of rack poles
        for contour in contours:
            points[i][0], points[i][1] = int(np.mean(contour[:, 0, 0])), int(np.mean(contour[:, 0, 1]))
            i += 1

        #sort each point by its distance from an anchor point (0,0)
        points = sorted(points, key = lambda x : (x[0]**2 + x[1]**2))


        #for more accurate sorting, sorted seperately as horizontal and vertical section racks
        horizontal_racks_pos = []


        #sort each point based on its distance from leftmost rack pole
        for i in range(len(points)):
            if points[i][1] < points[0][1] + ((3.5 / 2) * (warehouse_length_in_pixels)):
                horizontal_racks_pos.append(points[i])

        horizontal_racks_pos = np.array(horizontal_racks_pos)
        horizontal_racks_pos = sorted(horizontal_racks_pos, key = lambda x : x[0])


        vertical_racks_pos = []

        #sort each point in vertical rack section based on its distance from bottom top most rack pole
        for i in range(len(points)):
            if points[i][0] > points[-1][0] - ((3.5 / 2) * warehouse_width_in_pixels):
                vertical_racks_pos.append(points[i])

        vertical_racks_pos = np.array(vertical_racks_pos)
        vertical_racks_pos = sorted(vertical_racks_pos, key = lambda x : -x[1])


        #----coordinates for black strips---
        x1 = 0
        x2 = len(img[0])
        y1 = 0
        y2 = ceil((horizontal_racks_pos[0][1]) + (4.5 * warehouse_length_in_pixels))

        y_cropped = y2
        #top black strip
        img[y1:y2, x1:x2] = (0, 0, 0)

        optimal_pos[0][0] = ((3 * horizontal_racks_pos[0][0] + horizontal_racks_pos[1][0]) / 4) 
        optimal_pos[0][1] = ((warehouse_length * 1.75) / 42) + horizontal_racks_pos[0][1] + (3.5 * (warehouse_length_in_pixels))


        optimal_pos[1][0] = ((horizontal_racks_pos[0][0] + 3 * horizontal_racks_pos[1][0]) / 4)
        optimal_pos[1][1] = ((warehouse_length * 1.75) / 42) + horizontal_racks_pos[0][1] + (3.5 * (warehouse_length_in_pixels))


        optimal_pos[2][0] = ((3 * horizontal_racks_pos[2][0] + horizontal_racks_pos[3][0]) / 4)
        optimal_pos[2][1] = ((warehouse_length * 1.75) / 42) + horizontal_racks_pos[2][1] + (3.5 * (warehouse_length_in_pixels))


        optimal_pos[3][0] = ((horizontal_racks_pos[2][0] + 3 * horizontal_racks_pos[3][0]) / 4)
        optimal_pos[3][1] = ((warehouse_length * 1.75) / 42) + horizontal_racks_pos[2][1] + (3.5 * (warehouse_length_in_pixels))


        #cv2.circle(img, (int(horizontal_racks_pos[0][0]), int(horizontal_racks_pos[0][1])), 1, (0, 255, 0), -1)
        #plt.imshow(img)
        #plt.show()


        #print(points_new)

        x1 = ceil((vertical_racks_pos[0][0]) - (4.5 * warehouse_length_in_pixels))
        x2 = len(img[0])
        y1 = 0
        y2 = len(img)

        #print(optimal_pos[0])
        x_cropped = x1


        optimal_pos[4][0] = ((vertical_racks_pos[0][0] + vertical_racks_pos[1][0]) / 2) - (1.75 * warehouse_width_in_pixels) - ((3.5 / 31) *(len(img[0])))
        optimal_pos[4][1] = ((-vertical_racks_pos[0][1] + vertical_racks_pos[1][1]) / 4) + vertical_racks_pos[0][1]

        optimal_pos[5][0] = ((vertical_racks_pos[0][0] + vertical_racks_pos[1][0]) / 2) - (1.75 * warehouse_width_in_pixels) - ((3.5 / 31) *(len(img[0])))
        optimal_pos[5][1] = (((-vertical_racks_pos[0][1] + vertical_racks_pos[1][1]) / 4) * 3) + vertical_racks_pos[0][1]

        optimal_pos[6][0] = ((vertical_racks_pos[3][0] + vertical_racks_pos[2][0]) / 2) - (1.75 * warehouse_width_in_pixels) - ((3.5 / 31) *(len(img[0])))
        optimal_pos[6][1] = ((vertical_racks_pos[3][1] - vertical_racks_pos[2][1]) / 4) + vertical_racks_pos[2][1]

        optimal_pos[7][0] = ((vertical_racks_pos[3][0] + vertical_racks_pos[2][0]) / 2) - (1.75 * warehouse_width_in_pixels) - ((3.5 / 31) *(len(img[0])))
        optimal_pos[7][1] = (((vertical_racks_pos[3][1] - vertical_racks_pos[2][1]) / 4) * 3) + vertical_racks_pos[2][1]

        optimal_pos[8][0] = ((vertical_racks_pos[4][0] + vertical_racks_pos[5][0]) / 2) - (1.75 * warehouse_width_in_pixels) - ((3.5 / 31) *(len(img[0])))
        optimal_pos[8][1] = ((-vertical_racks_pos[4][1] + vertical_racks_pos[5][1]) / 4) + vertical_racks_pos[4][1]

        optimal_pos[9][0] = ((vertical_racks_pos[4][0] + vertical_racks_pos[5][0]) / 2) - (1.75 * warehouse_width_in_pixels) - ((3.5 / 31) *(len(img[0])))
        optimal_pos[9][1] = (((-vertical_racks_pos[4][1] + vertical_racks_pos[5][1]) / 4) * 3) + vertical_racks_pos[4][1] 

        #vertical stripe
        img[y1:y2, x1:x2] = (0, 0, 0)

        #bottom horizontal stripe
        img[ceil(warehouse_length - (warehouse_length_in_pixels)) : len(img), ceil(9 * warehouse_width_in_pixels) : len(img[0])] = (0, 0, 0)

        #left vertical stripe near wall
        img[0 : len(img), 0 : ceil(warehouse_length_in_pixels)] = (0, 0, 0)

        #black done


        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        #use thresh if needed
        _, img_gray = cv2.threshold(img_gray, 200, 254, cv2.THRESH_BINARY)

        # +1 after main white stripe
        img_gray[y_cropped : y_cropped + 1, ceil(warehouse_length_in_pixels) : x_cropped] = 255
        img_gray[y_cropped : ceil(warehouse_length - (warehouse_length_in_pixels)), x_cropped - 1: x_cropped] = 255
        img_gray[y_cropped : len(img), ceil(warehouse_length_in_pixels) : ceil(warehouse_length_in_pixels) + 1] = 255
        img_gray[ceil(warehouse_length - 1.5 * (warehouse_length_in_pixels)) - 1 : int(warehouse_length - 1.5 * (warehouse_length_in_pixels)), ceil(9 * warehouse_width_in_pixels) - 1 : x_cropped] = 255
        img_gray[int(warehouse_length - 1.5 * (warehouse_length_in_pixels)) - 1 : len(img), ceil(9 * warehouse_width_in_pixels - 1.5 * (warehouse_length_in_pixels)) - 1 : ceil((9 / 31) * len(img[0]) - 1.5 * (warehouse_length_in_pixels))] = 255

        #plt.imshow(img_gray[y_cropped : warehouse_length - int(warehouse_length_in_pixels), int(warehouse_length_in_pixels) : x_cropped], cmap="gray")
        #plt.show()


        contours, _ = cv2.findContours(img_gray[y_cropped : warehouse_length - int(warehouse_length_in_pixels), int(warehouse_length_in_pixels) : x_cropped], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #cv2.drawContours(img[y_cropped : warehouse_length - int(warehouse_length_in_pixels), int(warehouse_length_in_pixels) : x_cropped], contours, -1, (255, 0, 0), 1)




        #main white stripes of length 15
        img[y_cropped : y_cropped + ceil(1.5 * (warehouse_length_in_pixels)), ceil(warehouse_length_in_pixels) : x_cropped] = (0, 0, 0)
        img[y_cropped : ceil(warehouse_length - (warehouse_length_in_pixels)), x_cropped - ceil(1.5 * (warehouse_length_in_pixels)) : x_cropped] = (0, 0, 0)
        img[y_cropped : len(img), ceil(warehouse_length_in_pixels) : ceil(warehouse_length_in_pixels) + ceil(1.5 * (warehouse_length_in_pixels))] = (0, 0, 0)
        img[int(warehouse_length - 1.5 * (warehouse_length_in_pixels)) : warehouse_length, ceil(9 * ( 1 / 31) * len(img[0])) : x_cropped] = (0, 0, 0)
        img[int(warehouse_length - 1.5 * (warehouse_length_in_pixels)) : len(img), ceil(9 * warehouse_width_in_pixels - 1.5 * (warehouse_length_in_pixels)) : ceil(9 * warehouse_width_in_pixels)] = (0, 0, 0)

        #extending the white part by w/2 
        img[y_cropped + ceil(1.5 * (warehouse_length_in_pixels)) : y_cropped + ceil(1.5 * (warehouse_length_in_pixels)) + int(w / 2), ceil(warehouse_length_in_pixels) : x_cropped] = (0, 0, 0)
        img[y_cropped : ceil(warehouse_length - (warehouse_length_in_pixels)), x_cropped - ceil(1.5 * (warehouse_length_in_pixels)) - int(w / 2) : x_cropped - ceil(1.5 * (warehouse_length_in_pixels))] = (0, 0, 0)
        img[y_cropped : len(img), ceil(warehouse_length_in_pixels) + ceil(1.5 * (warehouse_length_in_pixels)) : ceil(warehouse_length_in_pixels) + ceil(1.5 * (warehouse_length_in_pixels)) + int(w / 2)] = (0, 0, 0)
        img[int(warehouse_length - 1.5 * (warehouse_length_in_pixels)) - int(w / 2) : int(warehouse_length - 1.5 * (warehouse_length_in_pixels)), ceil(9 * ( 1 / 31) * len(img[0])) - int(w / 2) : x_cropped] = (0, 0, 0)
        img[int(warehouse_length - 1.5 * (warehouse_length_in_pixels)) - int(w / 2) : len(img), ceil(9 * warehouse_width_in_pixels - 1.5 * (warehouse_length_in_pixels)) - int(w / 2) : ceil(9 * ( 1 / 31) * len(img[0]) - 1.5 * (warehouse_length_in_pixels))] = (0, 0, 0)


        #For obstacles
        #big white circle (black)
        for i in range(len(contours)):
            if 0 < cv2.contourArea(contours[i]) < 200:
                (x, y), _ = cv2.minEnclosingCircle(contours[i])
                cv2.circle(img[y_cropped : (warehouse_length - int(warehouse_length_in_pixels)), int(warehouse_length_in_pixels) : x_cropped], (int(x), int(y)), ceil(4.5 * (warehouse_length_in_pixels)) + int(w / 2), (0, 0, 0), -1)
                
        #big black circle (white)
        for i in range(len(contours)):
            if 0 < cv2.contourArea(contours[i]) < 200:
                (x, y), _ = cv2.minEnclosingCircle(contours[i])
                cv2.circle(img[y_cropped : (warehouse_length - int(warehouse_length_in_pixels)), int(warehouse_length_in_pixels) : x_cropped], (int(x), int(y)), ceil(2.5 * (warehouse_length_in_pixels)), (254, 254, 254), -1)
                


        img = 254 - img


        #to ensure the black region stays black even after white reg surrounding obstacle

        img[y1:y2, x1:x2] = (0, 0, 0)
        img[ceil(warehouse_length - (warehouse_length_in_pixels)) : len(img), ceil(9 * warehouse_width_in_pixels) : len(img[0])] = (0, 0, 0)
        img[0 : len(img), 0 : ceil(warehouse_length_in_pixels)] = (0, 0, 0)

        #rack detection
        x1 = 0
        x2 = len(img[0])
        y1 = 0
        y2 = ceil((horizontal_racks_pos[0][1]) + (4.5 * warehouse_length_in_pixels))

        y_cropped = y2

        img[y1:y2, x1:x2] = (0, 0, 0)


        x1 = ceil((vertical_racks_pos[0][0]) - (4.5 * warehouse_length_in_pixels))
        x2 = len(img[0])
        y1 = 0
        y2 = len(img)

        x_cropped = x1

        Minv = np.linalg.inv(M)

        optimal_pos[11][0] = optimal_pos[0][0] 
        optimal_pos[11][1] = len(img) / 4

        optimal_pos[12][0] = optimal_pos[0][0] 
        optimal_pos[12][1] = 2 * len(img) / 4

        optimal_pos[13][0] = optimal_pos[0][0]
        optimal_pos[13][1] = 3 * len(img) / 4


        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # move if obstacle is covering rack legs

        for i in range(4):
            optimal_pos[i][1] += (w / 4)
            circle = [[int(optimal_pos[i][1]), int(optimal_pos[i][0])], [int(optimal_pos[i][1])-1, int(optimal_pos[i][0])],[int(optimal_pos[i][1]), int(optimal_pos[i][0])-1] ,[int(optimal_pos[i][1])+1, int(optimal_pos[i][0])] ,[int(optimal_pos[i][1]), int(optimal_pos[i][0])+1]] 
            mean_int=0
            for pt in circle:
                mean_int+=img_gray[pt[0]][pt[1]]
            mean_int = int(mean_int / 5)
            while mean_int<254:
                optimal_pos[i][1] += 1
                circle = [[int(optimal_pos[i][1]), int(optimal_pos[i][0])], [int(optimal_pos[i][1])-1, int(optimal_pos[i][0])],[int(optimal_pos[i][1]), int(optimal_pos[i][0])-1] ,[int(optimal_pos[i][1])+1, int(optimal_pos[i][0])] ,[int(optimal_pos[i][1]), int(optimal_pos[i][0])+1]] 
                mean_int=0
                for pt in circle:
                    mean_int+=img_gray[pt[0]][pt[1]]
                mean_int = int(mean_int / 5)




        for i in range(4, 10):
            optimal_pos[i][0] -= (w / 4)
            circle = [[int(optimal_pos[i][1]), int(optimal_pos[i][0])], [int(optimal_pos[i][1])-1, int(optimal_pos[i][0])],[int(optimal_pos[i][1]), int(optimal_pos[i][0])-1] ,[int(optimal_pos[i][1])+1, int(optimal_pos[i][0])] ,[int(optimal_pos[i][1]), int(optimal_pos[i][0])+1]] 
            mean_int=0
            for pt in circle:
                mean_int+=img_gray[pt[0]][pt[1]]
            mean_int = int(mean_int / 5)
            while mean_int<254:
                optimal_pos[i][0] -= 1
                circle = [[int(optimal_pos[i][1]), int(optimal_pos[i][0])], [int(optimal_pos[i][1])-1, int(optimal_pos[i][0])],[int(optimal_pos[i][1]), int(optimal_pos[i][0])-1] ,[int(optimal_pos[i][1])+1, int(optimal_pos[i][0])] ,[int(optimal_pos[i][1]), int(optimal_pos[i][0])+1]] 
                mean_int=0
                for pt in circle:
                    mean_int+=img_gray[pt[0]][pt[1]]
                mean_int = int(mean_int / 5)


        for i in range(11, 14):
            circle = [[int(optimal_pos[i][1]), int(optimal_pos[i][0])], [int(optimal_pos[i][1])-1, int(optimal_pos[i][0])],[int(optimal_pos[i][1]), int(optimal_pos[i][0])-1] ,[int(optimal_pos[i][1])+1, int(optimal_pos[i][0])] ,[int(optimal_pos[i][1]), int(optimal_pos[i][0])+1]] 
            mean_int=0
            for pt in circle:
                mean_int+=img_gray[pt[0]][pt[1]]
            mean_int = int(mean_int / 5)
            while mean_int<254:
                optimal_pos[i][0] += 1
                circle = [[int(optimal_pos[i][1]), int(optimal_pos[i][0])], [int(optimal_pos[i][1])-1, int(optimal_pos[i][0])],[int(optimal_pos[i][1]), int(optimal_pos[i][0])-1] ,[int(optimal_pos[i][1])+1, int(optimal_pos[i][0])] ,[int(optimal_pos[i][1]), int(optimal_pos[i][0])+1]] 
                mean_int=0
                for pt in circle:
                    mean_int+=img_gray[pt[0]][pt[1]]
                mean_int = int(mean_int / 5)





        # !!! USE FOR SIDDU !!!
        img = cv2.rotate(img, cv2.ROTATE_180)
        optimal_pos[:, 0] = len(img[0]) - optimal_pos[:, 0]
        optimal_pos[:, 1] = len(img) - optimal_pos[:, 1]
        optimal_pos[4 : 10] = optimal_pos[4:10][::-1].copy()
        #-------


        optimal_pos[10][0] = (2 / 3) * optimal_pos[0][0] + (1 / 3) * optimal_pos[1][0]
        optimal_pos[10][1] = -5



        optimal_pos = get_transformed_optimal_pos(optimal_pos, Minv)

        img = 254 - img
        filter = cv2.warpPerspective(img, Minv, (len(ori_image[0]), len(ori_image)))
        filter = 254 - filter

        filter_gray = cv2.cvtColor(filter, cv2.COLOR_BGR2GRAY)


        for i in range(11):
            cv2.circle(filter, (int(optimal_pos[i][0]), int(optimal_pos[i][1])), 1, (255, 0, 0), -1)

        cv2.circle(filter, (int(optimal_pos[11][0]), int(optimal_pos[11][1])), 3, (0, 255, 0), -1)

        for i in range(11, 14):
            cv2.circle(filter, (int(optimal_pos[i][0]), int(optimal_pos[i][1])), 1, (0, 255, 0), -1)


        optimal_pos[:, 0] = origin_x + (optimal_pos[:, 0] * resolution)
        optimal_pos[:, 1] = origin_y + ((len(filter) - optimal_pos[:, 1]) * resolution)

        print(optimal_pos)


        plt.subplot(1, 2, 2)
        plt.imshow(filter)
        #plt.show()


        result = cv2.addWeighted(filter, 0.7, ori_image, 0.3, 0)

        plt.figure()
        plt.imshow(result)
        #plt.show()

        rack_file = os.path.expanduser("~/rack_positions.txt")

        with open(rack_file, "w") as file:
            
            file.write("I "+str(optimal_pos[10][0]) + "," + str(optimal_pos[10][1]) + ",0.0\n")
            file.write("I "+str(optimal_pos[10][0]) + "," + str(optimal_pos[10][1]) + ",-90.0\n")
            file.write("I "+str(optimal_pos[13][0]) + "," + str(optimal_pos[13][1]) + ",-90.0\n")
            file.write("I "+str(optimal_pos[12][0]) + "," + str(optimal_pos[12][1]) + ",-90.0\n")
            file.write("I " + str(optimal_pos[11][0]) + "," + str(optimal_pos[11][1]) + ",-90.0\n")
            for i in range(4):
                file.write("W "+str(optimal_pos[i][0]) + "," + str(optimal_pos[i][1]) + ",180.0\n")
            for i in range(4, 10):
                file.write("W "+str(optimal_pos[i][0]) + "," + str(optimal_pos[i][1]) + ",90.0\n")


        cv2.imwrite(os.path.expanduser('/home/team89/eternal-ros-architecture/src/navigation/navigation/arena_keepout.pgm'), filter_gray)


def main():
    rclpy.init()
    KeepoutFilter()
    rclpy.shutdown()


if __name__ == "__main__":
    main()