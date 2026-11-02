void run_ping(char *param_1)

{
  char local_58 [72];
  
  sprintf(local_58,"ping -c 1 %s",param_1);
  system(local_58);
  return;
}

