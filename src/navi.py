#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import sys 
from std_msgs.msg import String
from yaml import load
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import actionlib
from std_srvs.srv import Empty
import smach
import smach_ros

class Subscription(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                outcomes=['outcome1','outcome2'],
               # input_keys=['sub_target_in'],
                output_keys=['sub_target_out'])

        self.sub_message = rospy.Subscriber('/input_target', String, self.messageCB)
        self.message = String()
     
    def messageCB(self, receive_msg):
        self.message = receive_msg.data

    def execute(self, userdata):
        self.message = 'goal' 
        while not rospy.is_shutdown() and self.message == 'NULL':
            print"wait for topic..."
            rospy.sleep(2.0)
            
        rospy.loginfo("search LocationName")
        f = open('demo.yaml')
        location_dict = load(f)
        f.close()
        print self.message
        rospy.sleep(2.0)
        if self.message in location_dict:
            userdata.sub_target_out =location_dict[self.message]
            print location_dict[self.message]
            return 'outcome1'
        else:
            rospy.loginfo("NOT fount" + str(userdata.sub_target_out) + "> in LocationDict")
            return 'outcome2'

class NavigationAC(smach.State):
    def __init__(self):
        smach.State.__init__(self,
                outcomes=['outcome1','outcome3'],
                input_keys=['nav_target_in'])
        self.coord_list = []

    def execute(self, userdata):
        try:
            rospy.loginfo("Start Navigation")
            self.coord_list = userdata.nav_target_in
            ac = actionlib.SimpleActionClient('move_base',MoveBaseAction)
            ac.wait_for_server()
            clear_costmaps = rospy.ServiceProxy('move_base/clear_costmaps',Empty)
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
                    rospy.loginfo('Got ou of the obstacle')
                    rospy.sleep(1.0)
                elif state == 3:
                    rospy.loginfo('Navigation success!!')
                    return 'outcome3'
                elif state == 4:
                    if count == 10:
                        count = 0
                        rospy.loginfo('Navigation Failed')
                        return 'outcome1'
                    else:
                        rospy.loginfo('Buried in obstacle')
                        self.clear_costmaps()
                        rospy.loginfo('Clear Costmaps')
                        rospy.sleep(1.0)
                        count += 1
            rospy.sleep(2.0)
        except rospy.ROSInterruptException:
            pass
def main():
    sm = smach.StateMachine(outcomes=['outcome3'])
   # sm.userdata.sm_target = []
    with sm:
        smach.StateMachine.add('SUB', Subscription(),
                transitions={'outcome1':'NAV',
                    'outcome2':'SUB'},
                remapping={#'sub_target_in':'sm_target',
                    'sub_target_out':'sm_target'})
        smach.StateMachine.add('NAV',NavigationAC(),
                transitions={'outcome1':'SUB',
                    'outcome3':'SUB'},
                remapping={'nav_target_in':'sm_target'})
    outcome = sm.execute()
    roapy.loginfo('Finish"Navigation"')


if __name__ == '__main__':
    rospy.init_node('navigation_smach')
    main()
     



             






