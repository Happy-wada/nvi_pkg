#!/usr/bin/env python
# -*- coding utf-8 -*-

import rospy
import sys
import actionlib
from std_msgs.msg import String
from std_srvs.srv import Empty
from yaml import load
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import traceback


class Navigation():
    def __init__(self):
        self.coord_list = []
        self.sub_message = rospy.Subscriber('/input_target', String, self.messageCB)
        self.message = String()
        self.coord_list = []

    def messageCB(self,receive_msg):
        self.message = receive_msg.data

    def execute(self):
        self.message = 'goal'
        while not rospy.is_shutdown() and self.message == 'NULL':
            print"wait for topic..."
            rospy.sleep(2.0)
        return 1
    def searchLocationName(self):
        
        rospy.loginfo('search LocationName')
        f = open('demo.yaml')
        location_dict = load(f)
        f.close()
        print self.message
        rospy.sleep(2.0)
        if self.message in location_dict:
            print location_dict[self.message]
            rospy.loginfo("Return location_dict")
            self.coord_list = location_dict[self.message]
            return 2
        else:
            rospy.loginfo("NOT found<" + str(self.message) + "> in LocationDict")
            return 0


    def navigationAC(self):
        try:
            rospy.loginfo("Start Navigation")
            ac = actionlib.SimpleActionClient('move_base', MoveBaseAction)
            ac.wait_for_server()
            clear_costmaps = rospy.ServiceProxy('move_base/clear_costmaps', Empty)
            goal = MoveBaseGoal()
            goal.target_pose.header.frame_id = 'map'
            goal.target_pose.header.stamp = rospy.Time.now()
            goal.target_pose.pose.position.x = self.coord_list[0]
            goal.target_pose.pose.position.y = self.coord_list[1]
            goal.target_pose.pose.orientation.z = self.coord_list[2]
            goal.target_pose.pose.orientation.w = self.coord_list[3]
            rospy.wait_for_service('move_base/clear_costmaps')
            clear_costmaps()
            rospy.sleep(1.0)
            ac.send_goal(goal)
            count = 0
            while not rospy.is_shutdown():
                state = ac.get_state()
                if state == 1:
                    rospy.loginfo('Got out of the obstacle')
                    rospy.sleep(1.0)
                elif state == 3:
                    rospy.loginfo('Navigation success!!')
                    return 3
                elif state == 4:
                    if count == 10:
                        count = 0
                        rospy.loginfo('Navigation Failed')
                        return 2
                    else:
                        rospy.loginfo('Buried in obstacle')
                        self.clear_costmaps()
                        rospy.loginfo('Clear Costmaps')
                        rospy.sleep(1.0)
                        count += 1
            rospy.sleep(2.0)
        except rospy.ROSInterruptException:
            print(traceback.format_exc())
            pass

def main():
    nv = Navigation()
    state = 0
    rospy.loginfo('start "navigation"')
    while not rospy.is_shutdown() and not state == 3:
        if state == 0:
            state = nv.execute()
        if state == 1:
            state = nv.searchLocationName()
        if state == 2:
            state = nv.navigationAC()
    rospy.loginfo('Finish "Navigation"')


if __name__ == '__main__':
    rospy.init_node('nvi_pkg')
    main()


