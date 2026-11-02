void greet(char *param_1)

{
  char local_58 [64];
  char local_38 [32];
  
  strcpy(local_38,param_1);
  sprintf(local_58,"hello, %s",local_38);
  puts(local_58);
  return;
}

