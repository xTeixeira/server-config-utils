import subprocess
from dans_editor import Danseditor
from dhcp_editor import DHCPeditor

#this is a dict that formats group number codes to human readable text:
group_formatting = {'0':'Nenhum grupo atribuído', '1':'Erro no arquivo de configuracão. Favor checar os grupos manualmente.', 
'2':'Grupo Lista Negra', '3':'Grupo Diretoria', '4':'Grupo Lista Branca', '5':'Grupo Youtube'}

path_to_dans_config = '/etc/dansguardian/filtergroupslist' #change this to your dansguardian filtergroupslist file location
path_to_dhcp_config = '/etc/dhcpd.conf' #change this to your dhcpd.conf file location

ignore_main = False #used for situations where you want to ignore the main menu and go straight into a specific submenu

#these two bools are used to decide whether to reload dansguardian configs and restart dhcpd or not:
reload_dans = False
restart_dhcpd = False

#this is the index where to add MAC entries in the FORWARD table in iptables.
iptables_mac_index = '13'

while True:

	if not ignore_main:
		print('Bem-vindo ao utilitário de configuração do servidor.\nDigite o número correspondente ao serviço que deseja configurar:\n')
		print('1 - DHCP\n2 - Dansguardian\n3 - Bloqueio/desbloqueio de MACs\n4 - Sair\n')
		main_selection = input('Seleção: ')

	ignore_main = False

	if main_selection == '1':
		dhcpeditor = DHCPeditor(path_to_dhcp_config)

		print('Selecione uma opção:\n')
		print('1 - Adicionar uma entrada de IP estático.\n2 - Deletar uma entrada de IP estático.\n3 - Editar uma entrada de IP estático.\n4 - Retornar ao menu anterior.\n')
		dhcp_selection = input('Seleção: ')
		if dhcp_selection == '1':
			mac = input('Digite o MAC do PC: ')
			ip = input('Digite o IP que o PC Deverá receber: ')
			hostname = input('Digite o nome que o PC receberá no arquivo de configuração (hostname): ')

			dhcpeditor.add_entry(hostname, ip, mac)

			print('Entrada adicionada.\n')
			input()
			ignore_main = True
			restart_dhcpd = True

		elif dhcp_selection == '2':
			entry = input('Digite o MAC ou o IP do PC cuja entrada você deseja deletar: ')

			dhcpeditor.delete_entry(entry)
			print('Entrada deletada.\n')
			input()
			ignore_main = True
			restart_dhcpd = True

		elif dhcp_selection == '3':
			old = input('Digite o IP ou MAC que deseja substituir: ')
			new = input('Digite o novo IP ou MAC para substituir o antigo: ')

			result = dhcpeditor.edit_entry(old, new)
			if result == 0:
				print('Entrada editada.\n')
				restart_dhcpd = True
			else:
				print('O IP escolhido não está presente na lista do DHCP.')
			input()
			ignore_main = True



	elif main_selection == '2':
		danseditor = Danseditor(path_to_dans_config)

		print('Selecione uma opção:\n')
		print('1 - Checar grupo de liberação de um IP\n2 - Atribuir novo grupo de liberação a um IP\n3 - Tirar totalmente a liberação de um IP\n4 - Voltar ao menu anterior\n')
		dans_selection = input('Seleção: ')
		if dans_selection == '1':
			ip = input('Digite o IP: ')
			print(group_formatting[danseditor.check_group(ip)])
			input()
			ignore_main = True

		elif dans_selection == '2':
			ip = input('Digite o IP desejado: ')
			print('\nGrupos disponíveis (por padrão um IP sem grupo pertence ao grupo 1, que tem tudo bloqueado):\n')
			print('Grupo 2 - Lista Negra\nGrupo 3 - Diretoria\nGrupo 4 - Lista Branca\nGrupo 5 - Youtube\n')
			new_group = input('Digite o número do grupo a que deseja atribuir esse IP: ')
			result = danseditor.assign_group(ip, new_group)
			if result == 1:
				print('O IP escolhido já pertence a esse grupo.')
			else:
				print('Grupo atribuído.')
				reload_dans = True

			input()
			ignore_main = True

		elif dans_selection == '3':
			ip = input('Digite o IP que deseja tirar a liberação: ')
			danseditor.delete_assignment(ip)
			print('O IP não possui mais liberação.')
			reload_dans = True
			input()
			ignore_main = True

	elif main_selection == '3':
		print('Essa opção serve para permitir MACs específicos a ignorar o proxy e ter acesso direto à internet.\nSe algum usuário precisa de permissões de acesso mais liberais, é sempre indicado fazer isso pelo filtro Dansguardian e não por aqui. Usar somente em caso de exceções.\n')
		print('Selecione uma opção:\n1 - Listar MACs desbloqueados\n2 - Desbloquear MAC\n3 - Bloquear MAC\n4 - Voltar ao menu anterior\n')
		mac_selection = input('Seleção: ')

		if mac_selection == '1':
			print()
			out = subprocess.check_output (['iptables', '-L']).decode('utf-8')
			for line in out.splitlines():
				if line.find('MAC') != -1 and line.count('anywhere') == 2 and line.find('tcp dpt') == -1:
					print(line[-18:])

			ignore_main = True
			input()

		elif mac_selection == '2':
			mac = input('Digite o MAC a ser liberado: ')
			mac = mac.upper()
			subprocess.call(['iptables', '-I', 'FORWARD', iptables_mac_index, '-p', 'all', '-m', 'mac', '--mac-source', mac, '-j', 'ACCEPT'])
			print('MAC liberado.')
			ignore_main = True
			input()

		elif mac_selection == '3':
			mac = input('Digite o MAC a ser bloqueado: ')
			mac = mac.upper()
			subprocess.call(['iptables', '-D', 'FORWARD', '-p', 'all', '-m', 'mac', '--mac-source', mac, '-j', 'ACCEPT'])
			print('MAC bloqueado.')
			ignore_main = True
			input()

	elif main_selection == '4':
		if reload_dans:
			subprocess.call(['dansguardian', '-r'])
		if restart_dhcpd:
			subprocess.call(['/etc/rc.d/rc.dhcpd', 'restart']) #this restarts the dhcpd service on Slackware. You need to change the command according to your init system. e.g for systemd it would be 'systemctl', 'restart', 'dhcpd.service'.
		exit()
