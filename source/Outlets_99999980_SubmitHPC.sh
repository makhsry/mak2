#!/bin/bash 
# --------------------------------------------------------------------------------
# ################################################################################
#    nested functions area - do not edit unless needed. 
# 
# ----------------------------- are we in scratch otherwise leave 
is_under_scratch(){
	echo 'checking current directory, if not scratch, this script will terminate.'
	current_dir=$(pwd)
	if [[ "$current_dir" == *"scratch"* ]]; then
		echo "this script is sitting and running under 'scratch', continuing with tasks (otherwise it would terminate)."
	else
		echo "this script is NOT sitting and running under 'scratch'"
		echo "Terminating ...."
		exit
	fi
}
# ----------------------------- comsol default root cleanup 
comsolcleanup() {
    while true; do
        read -p "cleanup all files in comsol root i.e., ./.comsol/? (yes/no) [select no if there is any active job] " cleanupdecision
        case $cleanupdecision in
            "yes")
                echo "deleting all files in ./.comsol/ ...., it may take a while ...."
                rm -rvf $SCRATCH/.comsol/* $HOME/.comsol/*
                echo "deleted all files in ./.comsol/."
                break;;
            "no")
                echo "cleanup operation canceled."
                break;;
            * )
                echo "no answer provided or answer not recognized."
				echo "cleanup operation canceled."
                break;;
        esac
    done
}
# ----------------------------- collects username 
get_username(){
	username=$(whoami)
	while true; do
		read -p "are you $username? (yes/no) = " confirmusername
		case $confirmusername in
			"yes")
				echo "username confirmed. username is found correctly: $username"
				request_prompt=0
				break;;
			"no")
				echo "username is wrong, something is wrong with calling slurm."
				request_prompt=1
				break
				;;
			*)
				echo 'yes/no expected'
		esac 
	done
	# 
	if [ "$request_prompt" -eq 1 ]; then
		while true; do 
			echo "please type in your username"
			read -p "who are you? (username) = " usernamebyuser
			# 
			accounts=$(sacctmgr show assoc -P format=User,Account where user=$usernamebyuser | awk -F '|' -v user="$usernamebyuser" '$1 == user {print $2}')
			if [ -n "$accounts" ]; then
				echo "user $usernamebyuser exists and belongs to the following account(s):"
				echo "$accounts"
				username=$usernamebyuser
				break 
			else
				echo "user $usernamebyuser does not exist"
			fi 
		done
	fi 
}
# ----------------------------- collect account/allocation name - auto is faulty - set manual 
get_membership(){
	while true; do
		read -p "to which group/allocation you/$username belongs? (groupname/your boss/UBC:st-amadiseh-1/CC:def-madiseh) = " groupnamebyuser
		groupname=$groupnamebyuser
		if sacctmgr show assoc -P format=User,Account where user=$username,account=$groupname | grep -q "^$username|$groupname$"; then
			echo "you $username do belong to group $groupname"
			break 
		else
			echo "you $username do NOT belong to the specified group $groupname."
			echo "though you $username do belong to these groups: "
			sacctmgr show assoc -P format=User,Account where user=$username,account=$groupname
			echo "please try again."
		fi
	done 
}
# ----------------------------- collects job/series name, email 
get_job_extra_info(){
	while true; do 
		read -p "please type in an email to send job status updates to (user@domain.com) = " emailbyuser
		if [ -n $emailbyuser ]; then
			break 
		else
			echo 'you must provide an email. please try again.'
		fi
	done 
	# 
	while true; do 
		read -p "please type in a job name (array jobs not supported at this time) = " jobnamebyuser
		if [ -n $jobnamebyuser ]; then
			break 
		else
			echo 'you must provide a job name. please try again.'
		fi
	done 
	# 
	while true; do 
		read -p "please type in how many Nodes does this job require = (1 / 10) " nodesbyuser
		if [ -n $nodesbyuser ]; then
			break 
		else
			echo 'you must specify how many Nodes you need. please try again.'
		fi
	done 
}
# ----------------------------- watch mode on?  
watch_mode(){
	echo '>>> this script can be configured to monitor and resume jobs automatically.'
	echo 'option 						description'
	echo '1 							user specifies the wall-time. does NOT watch for job completion.'
	echo '2 							user specifies the wall-time. does watch for job completion and submits resume tasks automatically [if only failed due to TIMEOUT] as needed until done.'
	while true; do 
		read -p ">>> pick an option: (1/2) = " watchmode
		if [ -n $watchmode ]; then
			case $watchmode in
				"1")
					watch_me='no'
					IFS='-' read -p "please type in how much time hh-mm this job requires (NOTE the input pattern, separated by a hyphen)? = (hours-minutes) " hoursbyuser minutesbyuser
					break 
					;;
				"2")
					watch_me='yes'
					IFS='-' read -p "please type in how much time hh-mm this job requires (NOTE the input pattern, separated by a hyphen)? = (hours-minutes) " hoursbyuser minutesbyuser
					break 
					;;
				"99")
					echo "user confirmed enetering 99 mode."
					echo '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
					echo '!!!! this functionality may violate T&M of CC / ARC UBC !!!!'
					echo '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
					echo 'please provide passkey to use this feature' # change it to read 
					watch_me='yes'
					hoursbyuser='01'
					minutesbyuser='00'
					break 
					;;
				*)
					echo "option not recognized"
					;; 
			esac
		else
			echo 'you must pick an option. please try again.'
		fi
	done
}
# ----------------------------- build a .sh file 
initiate_sh_submit(){
	# --- preset text to echo >> 
	echo "#!/bin/bash" > submit_job.sh
	echo "#SBATCH --account=$groupname" >> submit_job.sh
	echo "#SBATCH --nodes=$nodesbyuser" >> submit_job.sh
	echo "#SBATCH --cpus-per-task=$cpusfromselections" >> submit_job.sh
	echo "#SBATCH --ntasks-per-node=1" >> submit_job.sh
	echo "#SBATCH --time=$hoursbyuser:$minutesbyuser:00" >> submit_job.sh
	echo "#SBATCH --job-name=$jobnamebyuser" >> submit_job.sh
	#
	if [ "$ramfromselections" != "NONE" ]; then
		echo "#SBATCH --mem=$ramfromselections" >> submit_job.sh
	fi
	#
	echo "#SBATCH --mail-user=$emailbyuser" >> submit_job.sh
	echo "#SBATCH --mail-type=ALL" >> submit_job.sh
	echo "#SBATCH --output=out.out" >> submit_job.sh
	echo "#SBATCH --error=err.err" >> submit_job.sh
	# 
	if [ "$archfromselections" != "NONE" ]; then
		echo "#SBATCH --constraint=$archfromselections" >> submit_job.sh
	fi
	#
 	# advising OS to handle large MPI memory unsafe process: comsol-java issue
	echo "ulimit -s unlimited" >> submit_job.sh
	#
	#for line in {0..12}; do
	#	content="line_$line"
	#	if [ "${!content}" != "SKIP" ]; then
	#		echo "${!content}" >> submit_job.sh
	#	fi 
	#done
}
# ----------------------------- determing where we are and what options we have - needs manual update if CC or UBC config changes. 
get_cluster_name(){
	cluster_name=$(scontrol show config | grep "^ClusterName" | awk -F= '{print $2}' | sed 's/^[ \t]*//;s/[ \t]*$//')
	echo "You are using $cluster_name". 
	# 
    while true; do
        read -p "do you confirm you are on $cluster_name? (yes/no) = " confirmclustername
        case $confirmclustername in
            "yes" )
                echo "user confirmed. clustername is found correctly: $cluster_name"
                break;;
            "no" )
                echo "user declined, something is wrong with calling slurm."
				echo "please pick one of the following cluster names manually when prompt."
				echo "sockeye, narval, beluga, cedar, graham, niagara"
				while true; do
        			read -p "we are on?: sockeye, narval, beluga, cedar, graham, niagara. = " clusternamebyuser
					if [ -n $clusternamebyuser ]; then
						case $clusternamebyuser in
							"sockeye")
								cluster_name="sockeye"
								break;;
							"narval")
								cluster_name="narval"
								break;;
							"beluga")
								cluster_name="beluga"
								break;;
							"cedar")
								cluster_name="cedar"
								break;;
							"graham")
								cluster_name="graham"
								break;;
							"niagara")
								cluster_name="niagara"
								break;;
							*)
								echo "$clusternamebyuser is not a recognizable cluster name, you have to provide architecture (Node, cpu, RAM, etc) manually!"
								cluster_name="manual"
								break;;
						esac 
					else
						echo 'you must provide a cluster namer. please try again.'
					fi
				done 
		esac
	done
}	# 
# ----------------------------- shows node state on cluster  
node_state(){
	echo pay attention to the timelimit the nodes are configured into, to make a wise time request when submitting your job. 
	echo nodes on $cluster are configured as shown bellow, note the timelimit and the number of nodes set to have such timelimits and then their availability
	#echo "columns are: PARTITION          AVAIL  TIMELIMIT   NODES(A/I/O/T) NODELIST"
 	echo "columns are: CPUS    MEMORY   GRES          NODES(A/I/O/T)  NODELIST"
	echo +++++
	#sinfo -s
 	sinfo -eO "CPUs:8,Memory:9,Gres:14,NodeAIOT:16,NodeList:50"
	echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
	echo do you want to see a full report on state of nodes? 
	echo ">>> this generate a long list, but should give you a more efficient node selection ability."
	read -p "do you want to see a report on state of individual nodes (yes/no)? = " showmenodestate
	case $showmenodestate in
		"yes")
			echo generating long text, scroll back to read throughly 
			#echo from list above, current state of nodes Allocated/Inuse/Other/Total is .... 
			#echo "columns are: CPUS    MEMORY   GRES          NODES(A/I/O/T)  NODELIST"
			#echo +++++
			#sinfo -eO "CPUs:8,Memory:9,Gres:14,NodeAIOT:16,NodeList:50"
			echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			echo idle nodes that are totally accessible right now are .... 
			echo "columns are: PARTITION          AVAIL  TIMELIMIT  NODES  STATE NODELIST"
			sinfo --state=idle
			echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			echo mixed nodes that might be accessible right now or shortly .... 
			echo "columns are: PARTITION          AVAIL  TIMELIMIT  NODES  STATE NODELIST"
			sinfo --state=mixed
			echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			echo here is a report on individual nodes 
			echo "columns are: HOSTNAMES FREE_MEM MEMORY AVAIL CPUS CPUS(A/I/O/T)"
			echo +++++
			sinfo -o "%n %m %a %c %C"
			echo +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			;;
		"no")
		;;
	esac
}
# ----------------------------- shows options on sockeye 
options_on_sockeye(){
	# 
	echo "option		RAMperCPU				AvailNodes			ARCH		isGPU"
	echo "1				6GB		=192GB/32cores		210				Skylake		 	 "
	echo "2				12GB	=384GB/32cores		8				Skylake		 	 "
	echo "3				24GB	=768GB/32cores		8				Skylake		 	 "
	echo "4				8GB		=192GB/24cores		6				Skylake		Yes	 "
	echo "5				4.8GB	=192GB/40cores		170				Cascade		 	 "
	echo "6				9.6GB	=384GB/40cores		8				Cascade		 	 "
	echo "7				19.2GB	=768GB/40cores		8				Cascade		 	 "
	echo "8				8GB		=192GB/24cores		44				Cascade		Yes	 "
	echo "  			8GB		=192GB/16cores		3				Skylake		login"
	echo "  			8GB		=192GB/16cores		2				Skylake		data "
	#
	while true; do
		read -p "pick an option number = " nodeselection
		if [ -n $nodeselection ]; then
			case $nodeselection in
				"1")
					echo "1				6GB=192GB/32cores		210				Skylake		No	 "
					cpusfromselections='32'
					ramfromselections='186G'
					archfromselections='NONE'
					break;;
				"2")
					echo "2				12GB=384GB/32cores		8				Skylake		No	 "
					cpusfromselections='32'
					ramfromselections='376G'
					archfromselections='NONE'
					break;;
				"3")
					echo "3				24GB=768GB/32cores		8				Skylake		No	 "
					cpusfromselections='32'
					ramfromselections='754G'
					archfromselections='NONE'
					break;;
				"4")
					echo "4				8GB=192GB/24cores		6				Skylake		Yes	 "
					echo 'not supported yet. declaring nothing. try again' 
					;;
				"5")
					echo "5				4.8GB=192GB/40cores		170				Cascade		No	 "
					cpusfromselections='40'
					ramfromselections='186G'
					archfromselections='NONE'
					break;;
				"6")
					echo "6				9.6GB=384GB/40cores		8				Cascade		No	 "
					cpusfromselections='40'
					ramfromselections='376G'
					archfromselections='NONE'
					break;;
				"7")
					echo "7				19.2GB=768GB/40cores	8				Cascade		No	 "
					cpusfromselections='40'
					ramfromselections='754G'
					archfromselections='NONE'
					break;;
				"8")
					echo "8				8GB=192GB/24cores		44				Cascade		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				*)
					echo "no answer provided or answer not recognized."
					echo "please try again."
					;;
			esac
		else
			echo 'you must pick an option from list.'
		fi 
	done
}
# ----------------------------- shows options on narval
options_on_narval(){
	echo "option		RAMperCPU				AvailNodes			ARCH		isGPU"
	echo "1				3.8GB	=249GB/64cores		1145			Rome		 	 "
	echo "2				31.3GB	=2009GB/64cores		33				Rome		 	 "
	echo "3				62.5GB	=4000GB/64cores		3				Rome		 	 "
	echo "4				7.7GB	=498GB/48cores		48				Milan		Yes	 "
	#
	while true; do
		read -p "pick an option number = " nodeselection
		if [ -n $nodeselection ]; then
			case $nodeselection in
				"1")
					echo "1				3.8GB	=249GB/64cores		1145			Rome		 	 "
					cpusfromselections='64'
					ramfromselections='249G'
					archfromselections='NONE'
					break;;
				"2")
					echo "2				31.3GB	=2009GB/64cores		33				Rome		 	 "
					cpusfromselections='64'
					ramfromselections='2009G'
					archfromselections='NONE'
					break;;
				"3")
					echo "3				62.5GB	=4000GB/64cores		3				Rome		 	 "
					cpusfromselections='64'
					ramfromselections='4000G'
					archfromselections='NONE'
					break;;
				"4")
					echo "4				7.7GB	=498GB/48cores		48				Milan		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				*)
					echo "no answer provided or answer not recognized."
					echo "please try again."
					;;
			esac
		else
			echo 'you must pick an option from list.'
		fi
	done
}
# ----------------------------- shows options on beluga
options_on_beluga(){
	echo "option		RAMperCPU				AvailNodes			ARCH		isGPU"
	echo "1				2.3GB	=92GB/40cores		160				Skylake		 	 "
	echo "2				4.65GB	=186GB/40cores		589				Skylake		 	 "
	echo "3				18.8GB	=752GB/40cores		53				Skylake		 	 "
	echo "4				4.65GB	=186GB/40cores		172				Skylake 	Yes	 "
	#
	while true; do
		read -p "pick an option number = " nodeselection
		if [ -n $nodeselection ]; then
			case $nodeselection in
				"1")
					echo "1				2.3GB	=92GB/40cores		160				Skylake		 	 "
					cpusfromselections='40'
					ramfromselections='92G'
					archfromselections='NONE'
					break;;
				"2")
					echo "2				4.65GB	=186GB/40cores		589				Skylake		 	 "
					cpusfromselections='40'
					ramfromselections='186G'
					archfromselections='NONE'
					break;;
				"3")
					echo "3				18.8GB	=752GB/40cores		53				Skylake		 	 "
					cpusfromselections='40'
					ramfromselections='752G'
					archfromselections='NONE'
					break;;
				"4")
					echo "4				4.65GB	=186GB/40cores		172				Skylake 	Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				*)
					echo "no answer provided or answer not recognized."
					echo "please try again."
					;;
			esac
		else
			echo 'you must pick an option from list.'
		fi
	done
}
# ----------------------------- shows options on cedar
options_on_cedar(){
	echo "option		RAMperCPU				AvailNodes			ARCH		isGPU"
	echo "1				3.9GB	=125GB/32cores		256				Broadwell		 	 "
	echo "2				7.8GB	=250GB/32cores		256				Broadwell		 	 "
	echo "3				15.6GB	=502GB/32cores		40				Broadwell		 	 "
	echo "4				47.18GB	=1510GB/32cores		16				Broadwell			 "
	echo "5				125GB	=4000GB/32cores		6				EPYC				 "
	echo "6				150GB	=6000GB/40cores		2				Cascade 			 "
	echo "7				5.2GB	=125GB/24cores		96				Broadwell  		Yes	 "
	echo "8				10.4GB	=250GB/24cores		32				Broadwell  		Yes	 "
	echo "9				5.8GB	=187GB/32cores		192				Cascade   		Yes	 "
	echo "10			3.8GB	=187GB/48cores		608				Skylake  			 "
	echo "11			3.8GB	=187GB/48cores		768				Cascade   			 "
	#
	while true; do
		read -p "pick an option number = " nodeselection
		if [ -n $nodeselection ]; then
			case $nodeselection in
				"1")
					echo "1				3.9GB	=125GB/32cores		256				Broadwell		 	 "
					cpusfromselections='32'
					ramfromselections='125G'
					archfromselections='broadwell'
					break;;
				"2")
					echo "2				7.8GB	=250GB/32cores		256				Broadwell		 	 "
					cpusfromselections='32'
					ramfromselections='250G'
					archfromselections='broadwell'
					break;;
				"3")
					echo "3				15.6GB	=502GB/32cores		40				Broadwell		 	 "
					cpusfromselections='32'
					ramfromselections='502G'
					archfromselections='broadwell'
					break;;
				"4")
					echo "4				47.18GB	=1510GB/32cores		16				Broadwell			 "
					cpusfromselections='32'
					ramfromselections='1510G'
					archfromselections='broadwell'
					break;;
				"5")
					echo "5				125GB	=4000GB/32cores		6				EPYC				 "
					cpusfromselections='32'
					ramfromselections='4000G'
					archfromselections='NONE'
					break;;
				"6")
					echo "6				150GB	=6000GB/40cores		2				Cascade 			 "
					cpusfromselections='40'
					ramfromselections='6000G'
					archfromselections='cascade'
					break;;
				"7")
					echo "7				5.2GB	=125GB/24cores		96				Broadwell  		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"8")
					echo "8				10.4GB	=250GB/24cores		32				Broadwell  		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"9")
					echo "9				5.8GB	=187GB/32cores		192				Cascade   		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"10")
					echo "10			3.8GB	=187GB/48cores		608				Skylake  			 "
					cpusfromselections='48'
					ramfromselections='187G'
					archfromselections='skylake'
					break;;
				"11")
					echo "11			3.8GB	=187GB/48cores		768				Cascade   			 "
					cpusfromselections='48'
					ramfromselections='187G'
					archfromselections='cascade'
					break;;
				*)
					echo "no answer provided or answer not recognized."
					echo "please try again."
					;;
			esac
		else
			echo 'you must pick an option from list.'
		fi
	done
}
# ----------------------------- shows options on nigara
options_on_nigara(){
	echo "no option selection with niagara, preset is:"
	echo " 				RAMperCPU				AvailNodes			ARCH		isGPU"
	echo " 				4.7GB	=188GB/40cores		2024 			Skylake		 	 "
	cpusfromselections='20'
	ramfromselections='NONE'
	archfromselections='NONE'
}
# ----------------------------- shows options on graham
options_on_graham(){
	echo "option		RAMperCPU				AvailNodes			ARCH		isGPU"
	echo "1				3.9GB	=125GB/32cores		903				Broadwell		 	 "
	echo "2				15.6GB	=502GB/32cores		24				Broadwell		 	 "
	echo "3				7.8GB	=250GB/32cores		56				Broadwell		 	 "
	echo "4				47.2GB	=3022GB/64cores		3				Broadwell			 "
	echo "5				3.8GB	=124GB/32cores		160				Broadwell		Yes	 "
	echo "6				6.6GB	=187GB/28cores		7				Skylake 		Yes	 "
	echo "7				9.4GB	=377GB/40cores		2				Cascade   		Yes	 "
	echo "8				11.6GB	=187GB/16cores		6				Skylake   		Yes	 "
	echo "9				4.25GB	=187GB/44cores		30				Cascade    		Yes	 "
	echo "10			4.25GB	=187GB/44cores		136				Cascade   			 "
	echo "11			15.6GB	=2000GB/128cores	1				EPYC   			Yes  "
	echo "12			8GB	    =256GB/32cores		2				Cascade    		Yes  "
	echo "13			1.95GB	=125GB/64cores		11				EPYC   			Yes  "
	#
	while true; do
		read -p "pick an option number = " nodeselection
		if [ -n $nodeselection ]; then
			case $nodeselection in
				"1")
					echo "1				3.9GB	=125GB/32cores		903				Broadwell		 	 "
					cpusfromselections='32'
					ramfromselections='125G'
					archfromselections='broadwell'
					break;;
				"2")
					echo "2				15.6GB	=502GB/32cores		24				Broadwell		 	 "
					cpusfromselections='32'
					ramfromselections='502G'
					archfromselections='broadwell'
					break;;
				"3")
					echo "3				7.8GB	=250GB/32cores		56				Broadwell		 	 "
					cpusfromselections='32'
					ramfromselections='250G'
					archfromselections='broadwell'
					break;;
				"4")
					echo "4				47.2GB	=3022GB/64cores		3				Broadwell			 "
					cpusfromselections='64'
					ramfromselections='3022G'
					archfromselections='broadwell'
					break;;
				"5")
					echo "5				3.8GB	=124GB/32cores		160				Broadwell		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"6")
					echo "6				6.6GB	=187GB/28cores		7				Skylake 		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"7")
					echo "7				9.4GB	=377GB/40cores		2				Cascade   		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"8")
					echo "8				11.6GB	=187GB/16cores		6				Skylake   		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"9")
					echo "9				4.25GB	=187GB/44cores		30				Cascade    		Yes	 "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"10")
					echo "10			4.25GB	=187GB/44cores		136				Cascade   			 "
					cpusfromselections='44'
					ramfromselections='187G'
					archfromselections='cascade'
					break;;
				"11")
					echo "11			15.6GB	=2000GB/128cores	1				EPYC   			Yes  "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"12")
					echo "12			8GB	    =256GB/32cores		2				Cascade    		Yes  "
					echo 'not supported yet. declaring nothing. try again'
					;;
				"13")
					echo "13			1.95GB	=125GB/64cores		11				EPYC   			Yes  "
					echo 'not supported yet. declaring nothing. try again'
					;;
				*)
					echo "no answer provided or answer not recognized."
					echo "please try again."
					;; 
			esac
		else
			echo 'you must pick an option from list.'
		fi
	done
}
# ----------------------------- show options for cluster 
show_cluster_options(){
	#
	node_state # show current state of nodes on the cluster 
	#
	echo "Here are the options for $cluster_name, please choose a number to build submission files."
	echo "(GPU nodes not supported at this time)"
	#
	case $cluster_name in
	 	"sockeye")
			options_on_sockeye
			;;
		# 
		"narval")
			options_on_narval
			;;
		#
		"beluga")
			options_on_beluga
			;;
		# 
		"niagara")
			options_on_nigara
			;;
		#
		"cedar")
			options_on_cedar
			;;
		# 
		"graham")
			options_on_graham
			;;
		#
		"manual")
			echo "please provide these set of info for $cluster_name."
			echo "not supportrd yet"
			;;
			#
	esac
}
# ----------------------------- what is comsol path 
where_is_comsol(){
	case $cluster_name in
		"sockeye")
			echo 'on ' $cluster_name ' SOCKEYE UBC ARC comsol is compiled manually at path (relative to home): //arc/project/st-amadiseh-1/comsol/comsol62/multiphysics/bin'
			echo 'writing comsol path to template sh file'
			echo "PATH2COMSOL='//arc/project/st-amadiseh-1/comsol/comsol62/multiphysics/bin'" >> submit_job.sh
			echo 'writing done.'
			#
			echo 'declaring and writing gcc, opemmpi and java path in template sh file'
			echo 'module load gcc' >> submit_job.sh
			echo 'module load openmpi' >> submit_job.sh
			echo 'module load openjdk/11.0.20.1_1' >> submit_job.sh
			echo 'writing done.'
			#
			CALL_COMSOL_AS="$""{PATH2COMSOL}/comsol"
			#
			;;
		*) 
			echo 'on ' $cluster_name ', comsol is loaded as a module'
			echo 'declaring and writing stabdard environment and comsol path in template sh file'
			if [ "$cluster_name" == "niagara" ]; then
				echo 'module load CCEnv' >> submit_job.sh
			fi 
			echo 'module load StdEnv/2020' >> submit_job.sh
			echo 'module load StdEnv/2023' >> submit_job.sh
			echo 'module load comsol/6.2' >> submit_job.sh
			# 
			CALL_COMSOL_AS="comsol"
			#
			if [ $cluster_name == "narval" ]; then
				echo 'NARVAL ' $cluster_name ' needs controll on external mpi forks. adding to template sh file'
				echo 'export I_MPI_COLL_EXTERNAL=0' >> submit_job.sh
				echo 'writing done.'
			fi
			#
			;;
	esac
}
# ----------------------------- get desk ready 
get_desk_ready(){
	case $confirmresume in
		"new")
			echo 'creating parent directory to put everything under: ' $whattimeisit
			mkdir -p $whattimeisit 
			echo 'created parent directory to put everything under: ' $whattimeisit
			echo 'making ' $whattimeisit ' accessible to all nodes' 
			chmod -R 755 $whattimeisit
			echo 'made ' $whattimeisit ' accessible to all nodes' 
			echo 'enetering ' $whattimeisit
			cd $whattimeisit # <<< relative pathes 
			pwd 
			echo 'enetered ' $whattimeisit
			echo 'creating temporary and recovery directories ....'
			mkdir -p tmp rec
			echo 'created temporary and recovery directories.'
			chmod -R 755 tmp rec
			echo 'made temporary and recovery directories accessible to all nodes.'
			RECDIR=rec #$whattimeisit/rec
			TMPDIR=tmp #$whattimeisit/tmp
			;;
		"resume")
			;;
	esac
}
# ----------------------------- prepare for a new job 
this_is_new_job(){
	COMSOL_CONTINUE=' '
	get_desk_ready 			# prepare desktop 
	# 
	comsolcleanup 			# cleaning comsol root directory 
	get_username			# who is the current user 
	get_membership			# who's your boss 
	get_cluster_name 		# geting the clustername and building an sh file 
	show_cluster_options 	# what is available on this cluster 
	get_job_extra_info	 	# getting extra info before building sh file 
	watch_mode				# watch mode on? or specify the wall-time 
	initiate_sh_submit		# creating bash submit file given user inputs/selections 	
	# 
	where_is_comsol 		# getting comsol path and settle
	#
 	echo "input file must be under (relative) ../, otherwise fails."
	read -p "please provide comsol INPUT file name (this script assumes input on relative path ../) = " inputmph
	if [ -n $inputmph ]; then
		echo 'creating a copy of input file ../ '$inputmph ' in ' $whattimeisit
		cp -v ../$inputmph .
		if [ $? -ne 0 ]; then
			echo "copy operation failed. please put input file ../ relative and try again."
   			echo "OR manually add the file to the directory once this script exists"
      			echo "directory to put the file is: _" $whattimeisit
		fi
	else
		echo 'you must provide input file name'
	fi 
	echo 'created a copy of file ../ '$inputmph ' in ' $whattimeisit
	# 
	echo 'if this is for one single study, provide study tag once prompt, otherwise type in +no+. (std2/no)'
	echo '(specifying multiple study not supported at this time)'
	while true; do 
		read -p "please provide study tag. (std2/no) = " runforstudy
		if [ -n $runforstudy ]; then
			case $runforstudy in 
				"no")
					echo 'no study tag provided, preparing for full'
					COMSOL_EXTRA_=' '
					#
					outputmph='solved_at_'$whattimeisit'_'$inputmph
					echo 'created OUTPUT filename as: ' $outputmph
					break 
					;;
				[std]*)
					echo 'study tag provided, preparing for study = ' $runforstudy
					COMSOL_EXTRA_='-study '$runforstudy
					outputmph='solved_at_'$whattimeisit'_'$runforstudy'_'$inputmph
					echo 'created OUTPUT filename as: ' $outputmph
					break
					;;
				*) 
					echo 'field left blanck'
			esac 
		else 
			echo 'field cannot left blanck'
		fi 
	done
}
# ----------------------------- this resumes a terminated job 
this_is_resume_job(){
	COMSOL_CONTINUE=' -recover -continue '
	while true; do 
		read -p "please provide terminated job recovery directory relative path = " recoverydir
		if [ -n $recoverydir ]; then
			RECDIR=$recoverydir
			break 
		else
			echo 'you must provide a path'
		fi 
	done 
	#
	while true; do 
		read -p "please provide terminated job temporary directory relative path = " temporarydir
		if [ -n $temporarydir ]; then
			TMPDIR=$temporarydir
			break 
		else
			echo 'you must provide a path'
		fi 
	done
	# 
	while true; do 
		read -p "please provide comsol INPUT file name = " inputmph
		if [ -n $inputmph ]; then
			break 
		else
			echo 'you must provide a finename'
		fi 
	done
	#
	while true; do 
		read -p "please provide comsol OUTPUT file name (>>> what set before, it is NOT a new name <<<) = " outputmph
		if [ -n $outputmph ]; then
			break 
		else
			echo 'you must provide a filename'
		fi 
	done 
	#
	get_desk_ready 			# prepare desktop 
	get_username			# who is the current user 
	get_membership			# who's your boss 
	get_cluster_name 		# geting the clustername 
	show_cluster_options 	# what is available on this cluster 
	get_job_extra_info	 	# getting extra info before building sh file 
	watch_mode				# watch mode on? or specify the wall-time 
	initiate_sh_submit		# creating bash submit file given user inputs/selections 	
	# 
	where_is_comsol 		# getting comsol path and settle 
	# 
	echo 'if this is for one single study, provide study tag once prompt, otherwise type in +no+. (std2/no)'
	echo '(specifying multiple study not supported at this time)'
	while true; do 
		read -p 'please provide study tag. (std2/no) = ' runforstudy
		if [ -n $runforstudy ]; then
			case $runforstudy in 
				[Nn]*)
					echo 'no study tag provided, preparing for full'
					COMSOL_EXTRA_=' '
					break;;
				[std]*)
					echo 'study tag provided, preparing for study = ' $runforstudy
					COMSOL_EXTRA_='-study '$runforstudy
					break;;
				*) 
					echo "field left empty"
			esac 
		else
			echo 'field cannot left blank'
		fi 
	done 
}
# ----------------------------- runs for a/list of specific parameter and value
running_for_specific_parameter(){
	read -p "is it a run for a specific parameter or list of parameters? (yes/no) = " itis4parameters
	while true; do 
		if [ -n $itis4parameters ]; then
			case $itis4parameters in 
				[Nn]*)
					echo 'no specific paramter is set and sent - this is a normal run'
					COMSOL_PARAMS_=' '
					break;;
				[Yy]*)
					echo 'setting and sending a (list of) paramter(s) to COMSOL command line.'
					read -p "how many parameters are to be specified? (1/2/.../n) = " itis4thismanyparameters
					echo 'be prepared to specifiy paramter details once prompted .....'
					list_of_parameters=""
					values_of_parameters=""
					for ((i=1; i<=itis4thismanyparameters; i++)); do
						read -p "enter NAME of parameter #$i: " current_parameter_name
						read -p "enter VALUE of parameter #$i ($current_parameter_name): " current_parameter_value
						if [ $i -eq 1 ]; then
							list_of_parameters="$current_parameter_name"
							values_of_parameters="$current_parameter_value"
						else
							list_of_parameters="$list_of_parameters,$current_parameter_name"
							values_of_parameters="$values_of_parameters,$current_parameter_value"
						fi
					done
					# 
					echo 'sent specifications to comsol call.'
					COMSOL_PARAMS_="-pname ${list_of_parameters} -plist ${values_of_parameters}"
					break;;
				*) 
					echo "field left empty"
			esac 
		else
			echo 'field cannot left blank'
		fi 
	done 
}
# ----------------------------- calling a method? 
caling_a_method(){
	read -p "does this run call a specific method? (yes/no) = " itis4method
	while true; do 
		if [ -n $itis4itis4method ]; then
			case $itis4itis4method in 
				[Nn]*)
					echo 'no specific method is set and sent - this is a normal run'
					COMSOL_METHOD_=' '
					break;;
				[Yy]*)
					read -p "enter NAME of method to be called: " method_name
					echo 'sent specifications to comsol call.'
					COMSOL_METHOD_="methodcall ${list_of_parameters}"
					break;;
				*) 
					echo "field left empty"
			esac 
		else
			echo 'field cannot left blank'
		fi 
	done 
}
# ----------------------------- running comsol 
submit_for_comsol(){
	logfilepath=$jobnamebyuser.log
	COMSOL_BASE_COMMAND="batch -mpibootstrap slurm -inputfile ${inputmph} -outputfile ${outputmph} -batchlog ${logfilepath} -tmpdir ${TMPDIR} -recoverydir ${RECDIR}  -alivetime 15"
	echo ${CALL_COMSOL_AS}' '${COMSOL_BASE_COMMAND}' '${COMSOL_EXTRA_}' '${COMSOL_CONTINUE}' '${COMSOL_PARAMS_}' '${COMSOL_METHOD_} >> 'submit_job.sh'
	#
	echo if you submit this jon NOW, it will probably starting at .... 
	echo "this info is very volatite, given how CCDB is configured (it forgets allocated nodes and reschdules everything every 15 minutes)"
	echo ++++++++
	sbatch --test-only submit_job.sh
	echo ++++++++
	echo moving to submit this job.
	echo for housekeeping purposes, renaming $whattimeisit to $jobnamebyuser'_'$whattimeisit. 
	cd ..
	mv $whattimeisit $jobnamebyuser'_'$whattimeisit
	echo renamed $whattimeisit to $jobnamebyuser'_'$whattimeisit. 
	cd $jobnamebyuser'_'$whattimeisit
	sbatch submit_job.sh
	#
	pwd
	echo current state of jobs under your account 
	squeue -u $username -l --start
}
# ----------------------------- watcher active? 
# function watcher - contact MAK to access the code 
# ----------------------------- user habit learner - add later 
# function learner - not yet 
##################################################################################
# --------------------------------------------------------------------------------
# this is main - steps actually taken in this script 
# --------------------------------------------------------------------------------
is_under_scratch # if not under scratch, leave immediately 
whattimeisit=$(date +"%Y%m%d_%H%M%S") # get time and date to organize files 
echo 'current date-time is : '$whattimeisit
# ----------------------------- is it a new run or terminated? 
while true; do 
	read -p "are you submitting a new job or resuming a terminated job? (new/resume) = " confirmresume
	if [ -n $recoverydir ]; then
		case $confirmresume in
			"new")
				echo "preparing for new submission."
				this_is_new_job 		# tasks for new job 
				running_for_specific_parameter
				submit_for_comsol 		# running comsol
				break;;
			"resume")
				echo "preparing for a terminated job."
				this_is_resume_job		# tasks for resume job
				running_for_specific_parameter 
				submit_for_comsol 		# running comsol
				break;;
			*) 
				echo "command not recognized or no input."
		esac
		break 
	else 
		echo 'you must pick a task'
	fi 
done 
# ----------------------------- watcher active? 
# function watcher - contact MAK to get the code 
# ----------------------------- user habit learner - add later 
# 
echo ALL DONE.
exit
# end of file 
